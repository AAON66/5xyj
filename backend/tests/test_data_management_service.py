"""Tests for data management service multi-value filtering and match status filter."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models.base import Base
from backend.app.models.enums import MatchStatus
from backend.app.models.import_batch import ImportBatch
from backend.app.models.match_result import MatchResult
from backend.app.models.normalized_record import NormalizedRecord
from backend.app.models.source_file import SourceFile
from backend.app.services.data_management_service import (
    get_filter_options,
    list_normalized_records,
)


@pytest.fixture()
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _make_batch(session: Session, batch_id: str | None = None) -> ImportBatch:
    bid = batch_id or str(uuid4())
    batch = ImportBatch(id=bid, batch_name=f"batch-{bid[:8]}", status="uploaded")
    session.add(batch)
    session.flush()
    return batch


def _make_source_file(session: Session, batch_id: str, sf_id: str | None = None) -> SourceFile:
    sid = sf_id or str(uuid4())
    sf = SourceFile(
        id=sid,
        batch_id=batch_id,
        file_name="test.xlsx",
        file_path="/tmp/test.xlsx",
        file_size=1024,
    )
    session.add(sf)
    session.flush()
    return sf


def _make_record(
    session: Session,
    batch_id: str,
    source_file_id: str,
    *,
    person_name: str = "Test",
    region: str = "guangzhou",
    company_name: str = "CompanyA",
    billing_period: str = "202602",
    record_id: str | None = None,
) -> NormalizedRecord:
    rid = record_id or str(uuid4())
    rec = NormalizedRecord(
        id=rid,
        batch_id=batch_id,
        source_file_id=source_file_id,
        source_row_number=1,
        person_name=person_name,
        region=region,
        company_name=company_name,
        billing_period=billing_period,
    )
    session.add(rec)
    session.flush()
    return rec


def _make_match_result(
    session: Session,
    batch_id: str,
    normalized_record_id: str,
    match_status: MatchStatus = MatchStatus.MATCHED,
) -> MatchResult:
    mr = MatchResult(
        id=str(uuid4()),
        batch_id=batch_id,
        normalized_record_id=normalized_record_id,
        match_status=match_status,
    )
    session.add(mr)
    session.flush()
    return mr


@pytest.fixture()
def seed_data(db_session: Session):
    """Seed test data: 3 records across 2 regions and 2 companies."""
    batch = _make_batch(db_session)
    sf = _make_source_file(db_session, batch.id)

    r1 = _make_record(
        db_session, batch.id, sf.id,
        person_name="Alice", region="guangzhou", company_name="CompanyA", billing_period="202602",
    )
    r2 = _make_record(
        db_session, batch.id, sf.id,
        person_name="Bob", region="shenzhen", company_name="CompanyB", billing_period="202603",
    )
    r3 = _make_record(
        db_session, batch.id, sf.id,
        person_name="Charlie", region="hangzhou", company_name="CompanyC", billing_period="202602",
    )

    # Match results: r1=MATCHED, r2=UNMATCHED, r3 has no match result
    _make_match_result(db_session, batch.id, r1.id, MatchStatus.MATCHED)
    _make_match_result(db_session, batch.id, r2.id, MatchStatus.UNMATCHED)

    db_session.commit()
    return {"batch": batch, "records": [r1, r2, r3]}


def test_list_records_multi_region(db_session: Session, seed_data):
    """Multi-region filter should return records from both selected regions."""
    result = list_normalized_records(
        db_session, regions=["guangzhou", "shenzhen"],
    )
    assert result.total == 2
    names = {item.person_name for item in result.items}
    assert names == {"Alice", "Bob"}


def test_list_records_multi_company(db_session: Session, seed_data):
    """Multi-company filter should return records from both selected companies."""
    result = list_normalized_records(
        db_session, company_names=["CompanyA", "CompanyB"],
    )
    assert result.total == 2
    names = {item.person_name for item in result.items}
    assert names == {"Alice", "Bob"}


def test_list_records_match_filter_matched(db_session: Session, seed_data):
    """match_filter='matched' should return only MATCHED records."""
    result = list_normalized_records(
        db_session, match_filter="matched",
    )
    assert result.total == 1
    assert result.items[0].person_name == "Alice"


def test_list_records_match_filter_unmatched(db_session: Session, seed_data):
    """match_filter='unmatched' should return records with no MatchResult or non-MATCHED status."""
    result = list_normalized_records(
        db_session, match_filter="unmatched",
    )
    assert result.total == 2
    names = {item.person_name for item in result.items}
    assert names == {"Bob", "Charlie"}


def test_filter_options_multi_region(db_session: Session, seed_data):
    """Multi-region filter options should return companies from both selected regions."""
    result = get_filter_options(
        db_session, regions=["guangzhou", "shenzhen"],
    )
    assert "CompanyA" in result.companies
    assert "CompanyB" in result.companies
    assert "CompanyC" not in result.companies


def test_list_records_match_filter_all(db_session: Session, seed_data):
    """match_filter=None should return all records without JOIN."""
    result = list_normalized_records(db_session)
    assert result.total == 3
