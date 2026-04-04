"""Tests for cross-period comparison in compare_service."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from backend.app.models import ImportBatch, NormalizedRecord, SourceFile
from backend.app.services.compare_service import compare_periods


def _seed_batch(db: Session, name: str = "test-batch") -> ImportBatch:
    batch = ImportBatch(batch_name=name)
    db.add(batch)
    db.flush()
    return batch


def _seed_source_file(db: Session, batch: ImportBatch, file_name: str = "test.xlsx") -> SourceFile:
    sf = SourceFile(batch_id=batch.id, file_name=file_name, file_size=1024, file_path="/tmp/test.xlsx")
    db.add(sf)
    db.flush()
    return sf


def _seed_record(
    db: Session,
    batch: ImportBatch,
    source_file: SourceFile,
    *,
    person_name: str,
    id_number: str,
    billing_period: str,
    region: str = "shenzhen",
    company_name: str = "TestCo",
    pension_company: Decimal | None = None,
    payment_base: Decimal | None = None,
    source_row_number: int = 1,
) -> NormalizedRecord:
    rec = NormalizedRecord(
        batch_id=batch.id,
        source_file_id=source_file.id,
        source_row_number=source_row_number,
        person_name=person_name,
        id_number=id_number,
        billing_period=billing_period,
        region=region,
        company_name=company_name,
        pension_company=pension_company,
        payment_base=payment_base,
        source_file_name="test.xlsx",
    )
    db.add(rec)
    db.flush()
    return rec


class TestComparePeriods:
    """Tests for compare_periods function."""

    def test_same_employee_same_values(self, db_session: Session):
        """Same employee in both periods with identical data -> SAME status."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        _seed_record(db_session, batch, sf, person_name="Alice", id_number="ID001",
                      billing_period="202601", pension_company=Decimal("1000.00"))
        _seed_record(db_session, batch, sf, person_name="Alice", id_number="ID001",
                      billing_period="202602", pension_company=Decimal("1000.00"), source_row_number=2)
        db_session.commit()

        result = compare_periods(db_session, "202601", "202602")
        assert result.left_period == "202601"
        assert result.right_period == "202602"
        assert result.same_row_count == 1
        assert result.total_row_count == 1
        assert result.changed_row_count == 0
        assert result.left_only_count == 0
        assert result.right_only_count == 0

    def test_changed_employee(self, db_session: Session):
        """Employee with changed values across periods -> CHANGED status."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        _seed_record(db_session, batch, sf, person_name="Bob", id_number="ID002",
                      billing_period="202601", pension_company=Decimal("1000.00"))
        _seed_record(db_session, batch, sf, person_name="Bob", id_number="ID002",
                      billing_period="202602", pension_company=Decimal("2000.00"), source_row_number=2)
        db_session.commit()

        result = compare_periods(db_session, "202601", "202602")
        assert result.changed_row_count == 1
        assert result.same_row_count == 0
        changed_row = result.rows[0]
        assert changed_row.diff_status == "changed"
        assert "pension_company" in changed_row.different_fields

    def test_left_only_and_right_only(self, db_session: Session):
        """Employee in only one period -> left_only or right_only."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        _seed_record(db_session, batch, sf, person_name="Left", id_number="ID003",
                      billing_period="202601")
        _seed_record(db_session, batch, sf, person_name="Right", id_number="ID004",
                      billing_period="202602", source_row_number=2)
        db_session.commit()

        result = compare_periods(db_session, "202601", "202602")
        assert result.left_only_count == 1
        assert result.right_only_count == 1
        assert result.total_row_count == 2

    def test_filter_by_region(self, db_session: Session):
        """Filtering by region should exclude records from other regions."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        _seed_record(db_session, batch, sf, person_name="A", id_number="ID010",
                      billing_period="202601", region="shenzhen")
        _seed_record(db_session, batch, sf, person_name="A", id_number="ID010",
                      billing_period="202602", region="shenzhen", source_row_number=2)
        _seed_record(db_session, batch, sf, person_name="B", id_number="ID011",
                      billing_period="202601", region="guangzhou", source_row_number=3)
        _seed_record(db_session, batch, sf, person_name="B", id_number="ID011",
                      billing_period="202602", region="guangzhou", source_row_number=4)
        db_session.commit()

        result = compare_periods(db_session, "202601", "202602", region="shenzhen")
        assert result.total_row_count == 1

    def test_filter_by_company_name(self, db_session: Session):
        """Filtering by company_name should exclude other companies."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        _seed_record(db_session, batch, sf, person_name="C", id_number="ID020",
                      billing_period="202601", company_name="Alpha")
        _seed_record(db_session, batch, sf, person_name="C", id_number="ID020",
                      billing_period="202602", company_name="Alpha", source_row_number=2)
        _seed_record(db_session, batch, sf, person_name="D", id_number="ID021",
                      billing_period="202601", company_name="Beta", source_row_number=3)
        db_session.commit()

        result = compare_periods(db_session, "202601", "202602", company_name="Alpha")
        assert result.total_row_count == 1
        assert result.same_row_count == 1

    def test_summary_has_correct_period_metadata(self, db_session: Session):
        """PeriodCompareRead should include period metadata and fields."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        _seed_record(db_session, batch, sf, person_name="E", id_number="ID030",
                      billing_period="202601", pension_company=Decimal("500.00"))
        _seed_record(db_session, batch, sf, person_name="E", id_number="ID030",
                      billing_period="202602", pension_company=Decimal("500.00"), source_row_number=2)
        db_session.commit()

        result = compare_periods(db_session, "202601", "202602")
        assert result.left_period == "202601"
        assert result.right_period == "202602"
        assert isinstance(result.fields, list)
        assert len(result.fields) > 0

    def test_empty_periods(self, db_session: Session):
        """Comparing two periods with no data should return empty result."""
        result = compare_periods(db_session, "202601", "202602")
        assert result.total_row_count == 0
        assert result.rows == []

    def test_summary_groups_populated(self, db_session: Session):
        """summary_groups should be populated with per-company/region aggregation."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        _seed_record(db_session, batch, sf, person_name="F", id_number="ID040",
                      billing_period="202601", company_name="Co1", region="shenzhen")
        _seed_record(db_session, batch, sf, person_name="F", id_number="ID040",
                      billing_period="202602", company_name="Co1", region="shenzhen", source_row_number=2)
        db_session.commit()

        result = compare_periods(db_session, "202601", "202602")
        assert len(result.summary_groups) >= 1
        group = result.summary_groups[0]
        assert group.total_count == 1
