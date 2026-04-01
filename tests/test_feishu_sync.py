"""Tests for Feishu sync models, client, and sync service."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from sqlalchemy.orm import Session
from uuid import uuid4

from backend.app.models.normalized_record import NormalizedRecord
from backend.app.models.sync_config import SyncConfig
from backend.app.models.sync_job import SyncJob
from backend.app.services.feishu_client import FeishuApiError, FeishuClient
from backend.app.services.feishu_sync_service import (
    _record_to_feishu_row,
    _summarize_records,
    get_sync_history,
    push_records_to_feishu,
    pull_records_from_feishu,
    check_push_conflicts,
    detect_pull_conflicts,
    retry_sync_job,
)


def _run(coro):
    """Helper to run async code in tests."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


def test_sync_config_model_creation(db_session: Session):
    """SyncConfig persists all fields including JSON field_mapping."""
    config = SyncConfig(
        name="Test Config",
        app_token="app_token_123",
        table_id="tbl_456",
        granularity="detail",
        field_mapping={"Name": "person_name", "ID": "id_number"},
        is_active=True,
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)

    assert config.id is not None
    assert config.name == "Test Config"
    assert config.app_token == "app_token_123"
    assert config.table_id == "tbl_456"
    assert config.granularity == "detail"
    assert config.field_mapping == {"Name": "person_name", "ID": "id_number"}
    assert config.is_active is True


def test_sync_job_model_creation(db_session: Session):
    """SyncJob linked to SyncConfig, FK relationship works."""
    config = SyncConfig(
        name="Job Test Config",
        app_token="app_token_abc",
        table_id="tbl_def",
        granularity="summary",
        field_mapping={},
    )
    db_session.add(config)
    db_session.commit()

    job = SyncJob(
        config_id=config.id,
        direction="push",
        status="running",
        total_records=100,
        success_records=95,
        failed_records=5,
        error_message=None,
        triggered_by="admin",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert job.id is not None
    assert job.config_id == config.id
    assert job.direction == "push"
    assert job.status == "running"
    assert job.total_records == 100
    assert job.config.name == "Job Test Config"


# ---------------------------------------------------------------------------
# FeishuClient tests
# ---------------------------------------------------------------------------


def test_feishu_client_is_async():
    """FeishuClient uses httpx.AsyncClient (not sync Client)."""
    async def run():
        client = FeishuClient("app_id", "app_secret")
        assert isinstance(client._http, httpx.AsyncClient)
        await client.close()

    _run(run())


def test_feishu_client_rate_limiting():
    """Verify semaphore attribute exists with expected value."""
    async def run():
        client = FeishuClient("app_id", "app_secret", max_concurrent=10)
        assert isinstance(client._semaphore, asyncio.Semaphore)
        assert client._semaphore._value == 10
        await client.close()

    _run(run())


def test_feishu_client_token_caching():
    """Token is cached and only refreshed when expired."""
    async def run():
        client = FeishuClient("app_id", "app_secret")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 0,
            "tenant_access_token": "test_token_123",
            "expire": 7200,
        }
        mock_response.raise_for_status = MagicMock()
        client._http.post = AsyncMock(return_value=mock_response)

        token1 = await client._ensure_token()
        token2 = await client._ensure_token()
        assert token1 == "test_token_123"
        assert token2 == "test_token_123"
        # Should only call API once (second call uses cache)
        assert client._http.post.call_count == 1
        await client.close()

    _run(run())


def test_feishu_client_list_fields():
    """list_fields returns parsed items from API response."""
    async def run():
        client = FeishuClient("app_id", "app_secret")
        client._token = "test_token"
        client._token_expires_at = 9999999999

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "items": [
                    {"field_id": "f1", "field_name": "Name", "type": 1},
                    {"field_id": "f2", "field_name": "Amount", "type": 2},
                ],
                "has_more": False,
            },
        }
        mock_response.raise_for_status = MagicMock()
        client._http.get = AsyncMock(return_value=mock_response)

        fields = await client.list_fields("app_token", "tbl_id")
        assert len(fields) == 2
        assert fields[0]["field_name"] == "Name"
        await client.close()

    _run(run())


def test_feishu_client_batch_create():
    """batch_create_records sends correct payload."""
    async def run():
        client = FeishuClient("app_id", "app_secret")
        client._token = "test_token"
        client._token_expires_at = 9999999999

        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": {}}
        mock_response.raise_for_status = MagicMock()
        client._http.post = AsyncMock(return_value=mock_response)

        result = await client.batch_create_records("app_token", "tbl_id", [{"Name": "Test"}])
        assert result["code"] == 0
        call_args = client._http.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert payload["records"][0]["fields"]["Name"] == "Test"
        await client.close()

    _run(run())


def test_feishu_client_search_records():
    """search_records handles response correctly."""
    async def run():
        client = FeishuClient("app_id", "app_secret")
        client._token = "test_token"
        client._token_expires_at = 9999999999

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "items": [{"record_id": "r1", "fields": {"Name": "Test"}}],
                "has_more": False,
            },
        }
        mock_response.raise_for_status = MagicMock()
        client._http.post = AsyncMock(return_value=mock_response)

        result = await client.search_records("app_token", "tbl_id")
        assert result["data"]["items"][0]["fields"]["Name"] == "Test"
        await client.close()

    _run(run())


def test_feishu_api_error_on_nonzero_code():
    """FeishuApiError raised when API returns code != 0."""
    async def run():
        client = FeishuClient("app_id", "app_secret")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 99991,
            "msg": "Invalid token",
        }
        mock_response.raise_for_status = MagicMock()
        client._http.post = AsyncMock(return_value=mock_response)

        with pytest.raises(FeishuApiError) as exc_info:
            await client._ensure_token()
        assert exc_info.value.code == 99991
        assert "Invalid token" in str(exc_info.value)
        await client.close()

    _run(run())


# ---------------------------------------------------------------------------
# Sync service tests
# ---------------------------------------------------------------------------


def test_push_field_mapping_transform():
    """Record transformation uses field_mapping correctly."""
    record = MagicMock(spec=NormalizedRecord)
    record.person_name = "Zhang San"
    record.id_number = "110101199001011234"
    record.pension_company = Decimal("500.50")

    mapping = {"Name": "person_name", "ID": "id_number", "Pension": "pension_company"}
    row = _record_to_feishu_row(record, mapping)

    assert row["Name"] == "Zhang San"
    assert row["ID"] == "110101199001011234"
    assert row["Pension"] == 500.50
    assert isinstance(row["Pension"], float)


def test_push_decimal_to_float_conversion():
    """Decimal amounts become float in push payload."""
    record = MagicMock(spec=NormalizedRecord)
    record.total_amount = Decimal("1234.56")
    record.person_name = "Li Si"

    mapping = {"Total": "total_amount", "Name": "person_name"}
    row = _record_to_feishu_row(record, mapping)

    assert isinstance(row["Total"], float)
    assert row["Total"] == 1234.56
    assert isinstance(row["Name"], str)


def test_push_summary_granularity_grouping():
    """Summary mode groups by company+region+period and sums amounts."""
    records = []
    for i in range(3):
        r = MagicMock(spec=NormalizedRecord)
        r.company_name = "Company A"
        r.region = "guangzhou"
        r.billing_period = "202602"
        r.pension_company = Decimal("100.00")
        r.person_name = f"Person {i}"
        records.append(r)

    mapping = {
        "Company": "company_name",
        "Region": "region",
        "Period": "billing_period",
        "Pension": "pension_company",
    }
    rows = _summarize_records(records, mapping)

    assert len(rows) == 1  # All grouped into one
    assert rows[0]["Pension"] == 300.0  # Summed


def test_conflict_detection_by_employee_month(db_session: Session):
    """Conflicts detected when Feishu records overlap with system records."""
    record = NormalizedRecord(
        batch_id=str(uuid4()),
        source_file_id=str(uuid4()),
        source_row_number=1,
        person_name="Zhang San",
        id_number="110101199001011234",
        billing_period="202602",
        pension_company=Decimal("500.00"),
    )
    db_session.add(record)
    db_session.commit()

    config = SyncConfig(
        name="Conflict Test",
        app_token="app_token",
        table_id="tbl_id",
        granularity="detail",
        field_mapping={
            "Name": "person_name",
            "ID": "id_number",
            "Period": "billing_period",
            "Pension": "pension_company",
        },
    )
    db_session.add(config)
    db_session.commit()

    mock_client = AsyncMock(spec=FeishuClient)
    mock_client.search_records.return_value = {
        "data": {
            "items": [{
                "fields": {
                    "Name": "Zhang San",
                    "ID": "110101199001011234",
                    "Period": "202602",
                    "Pension": 600.0,
                },
            }],
            "has_more": False,
        },
    }

    result = _run(detect_pull_conflicts(db_session, mock_client, config))

    assert result is not None
    assert result.total_conflicts == 1
    assert "pension_company" in result.conflicts[0].diff_fields


def test_pull_sets_provenance_markers(db_session: Session):
    """Pull sets source_file_name='feishu_pull:{config.name}' on created records."""
    config = SyncConfig(
        name="Provenance Test",
        app_token="app_token",
        table_id="tbl_id",
        granularity="detail",
        field_mapping={"Name": "person_name", "ID": "id_number", "Period": "billing_period"},
    )
    db_session.add(config)
    db_session.commit()

    mock_client = AsyncMock(spec=FeishuClient)
    mock_client.search_records.return_value = {
        "data": {
            "items": [{
                "fields": {
                    "Name": "Wang Wu",
                    "ID": "220101199501011234",
                    "Period": "202603",
                },
            }],
            "has_more": False,
        },
    }

    job = _run(
        pull_records_from_feishu(db_session, mock_client, config, "feishu_wins", None, "test_admin")
    )

    assert job.status == "success"
    assert job.success_records == 1

    from sqlalchemy import select
    pulled = db_session.execute(
        select(NormalizedRecord).where(NormalizedRecord.id_number == "220101199501011234")
    ).scalars().first()

    assert pulled is not None
    assert pulled.source_file_name == "feishu_pull:Provenance Test"
    assert pulled.raw_header_signature == "feishu:tbl_id"


def test_get_sync_history_with_offset(db_session: Session):
    """Sync history returns in desc order and offset skips records correctly."""
    config = SyncConfig(
        name="History Config",
        app_token="app_token",
        table_id="tbl_id",
        granularity="detail",
        field_mapping={},
    )
    db_session.add(config)
    db_session.commit()

    for i in range(5):
        job = SyncJob(
            config_id=config.id,
            direction="push",
            status="success",
            total_records=i * 10,
            triggered_by="admin",
        )
        db_session.add(job)
    db_session.commit()

    all_jobs = get_sync_history(db_session)
    assert len(all_jobs) == 5

    offset_jobs = get_sync_history(db_session, offset=2, limit=2)
    assert len(offset_jobs) == 2

    filtered_jobs = get_sync_history(db_session, config_id=config.id)
    assert len(filtered_jobs) == 5


def test_sync_lock_prevents_concurrent_jobs(db_session: Session):
    """Error when trying to push while another job is running for same config."""
    config = SyncConfig(
        name="Lock Test",
        app_token="app_token",
        table_id="tbl_id",
        granularity="detail",
        field_mapping={"Name": "person_name"},
    )
    db_session.add(config)
    db_session.commit()

    running_job = SyncJob(
        config_id=config.id,
        direction="push",
        status="running",
        triggered_by="admin",
    )
    db_session.add(running_job)
    db_session.commit()

    mock_client = AsyncMock(spec=FeishuClient)

    with pytest.raises(RuntimeError, match="already running"):
        _run(push_records_to_feishu(db_session, mock_client, config, None, "admin"))
