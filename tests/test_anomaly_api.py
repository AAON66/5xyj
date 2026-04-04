"""Tests for anomaly API endpoints."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from backend.app.core.auth import issue_access_token
from backend.app.models import AnomalyRecord, ImportBatch, NormalizedRecord, SourceFile
from tests.conftest import TEST_SECRET_KEY


def _admin_token() -> str:
    token, _ = issue_access_token(TEST_SECRET_KEY, "testadmin", "admin", 480)
    return token


def _hr_token() -> str:
    token, _ = issue_access_token(TEST_SECRET_KEY, "testhr", "hr", 480)
    return token


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _seed_data(db: Session):
    """Seed normalized records for two periods."""
    batch = ImportBatch(batch_name="test-batch")
    db.add(batch)
    db.flush()
    sf = SourceFile(batch_id=batch.id, file_name="test.xlsx", file_size=1024, file_path="/tmp/test.xlsx")
    db.add(sf)
    db.flush()

    # Employee with large payment_base change (5000 -> 8000 = 60%)
    for period, base, row in [("202601", Decimal("5000.00"), 1), ("202602", Decimal("8000.00"), 2)]:
        db.add(NormalizedRecord(
            batch_id=batch.id,
            source_file_id=sf.id,
            source_row_number=row,
            person_name="Alice",
            id_number="ID001",
            billing_period=period,
            region="shenzhen",
            company_name="TestCo",
            payment_base=base,
            source_file_name="test.xlsx",
        ))
    db.commit()


class TestPostDetect:
    """Test POST /api/v1/anomalies/detect."""

    def test_detect_returns_anomalies(self, test_client, db_session, seed_test_admin):
        _seed_data(db_session)
        resp = test_client.post(
            "/api/v1/anomalies/detect",
            json={"left_period": "202601", "right_period": "202602"},
            headers=_auth_header(_admin_token()),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) > 0
        # Should detect payment_base anomaly
        fields = [a["field_name"] for a in body["data"]]
        assert "payment_base" in fields

    def test_detect_requires_auth(self, test_client):
        resp = test_client.post(
            "/api/v1/anomalies/detect",
            json={"left_period": "202601", "right_period": "202602"},
        )
        assert resp.status_code == 401


class TestGetAnomalies:
    """Test GET /api/v1/anomalies."""

    def test_list_with_pagination(self, test_client, db_session, seed_test_admin):
        # Create some anomaly records directly
        for i in range(3):
            db_session.add(AnomalyRecord(
                employee_identifier=f"ID{i}",
                left_period="202601",
                right_period="202602",
                field_name="payment_base",
                change_percent=60.0,
                threshold_percent=15.0,
                status="pending",
            ))
        db_session.commit()

        resp = test_client.get(
            "/api/v1/anomalies?page=0&page_size=2",
            headers=_auth_header(_admin_token()),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 2
        assert body["pagination"]["total"] == 3

    def test_list_filter_by_status(self, test_client, db_session, seed_test_admin):
        db_session.add(AnomalyRecord(
            employee_identifier="ID0",
            left_period="202601",
            right_period="202602",
            field_name="payment_base",
            change_percent=60.0,
            threshold_percent=15.0,
            status="pending",
        ))
        db_session.add(AnomalyRecord(
            employee_identifier="ID1",
            left_period="202601",
            right_period="202602",
            field_name="payment_base",
            change_percent=60.0,
            threshold_percent=15.0,
            status="confirmed",
        ))
        db_session.commit()

        resp = test_client.get(
            "/api/v1/anomalies?status=pending",
            headers=_auth_header(_admin_token()),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["pagination"]["total"] == 1

    def test_list_requires_auth(self, test_client):
        resp = test_client.get("/api/v1/anomalies")
        assert resp.status_code == 401


class TestPatchStatus:
    """Test PATCH /api/v1/anomalies/status."""

    def test_batch_update_status(self, test_client, db_session, seed_test_admin):
        records = []
        for i in range(2):
            rec = AnomalyRecord(
                employee_identifier=f"ID{i}",
                left_period="202601",
                right_period="202602",
                field_name="payment_base",
                change_percent=60.0,
                threshold_percent=15.0,
                status="pending",
            )
            db_session.add(rec)
            records.append(rec)
        db_session.commit()
        for rec in records:
            db_session.refresh(rec)

        resp = test_client.patch(
            "/api/v1/anomalies/status",
            json={
                "status": "confirmed",
                "anomaly_ids": [rec.id for rec in records],
            },
            headers=_auth_header(_admin_token()),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["updated_count"] == 2

    def test_hr_can_update_status(self, test_client, db_session, seed_test_hr):
        rec = AnomalyRecord(
            employee_identifier="ID0",
            left_period="202601",
            right_period="202602",
            field_name="payment_base",
            change_percent=60.0,
            threshold_percent=15.0,
            status="pending",
        )
        db_session.add(rec)
        db_session.commit()
        db_session.refresh(rec)

        resp = test_client.patch(
            "/api/v1/anomalies/status",
            json={"status": "excluded", "anomaly_ids": [rec.id]},
            headers=_auth_header(_hr_token()),
        )
        assert resp.status_code == 200

    def test_update_requires_auth(self, test_client):
        resp = test_client.patch(
            "/api/v1/anomalies/status",
            json={"status": "confirmed", "anomaly_ids": ["fake-id"]},
        )
        assert resp.status_code == 401
