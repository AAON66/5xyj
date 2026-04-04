"""Tests for anomaly detection service."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from backend.app.models import AnomalyRecord, ImportBatch, NormalizedRecord, SourceFile
from backend.app.services.anomaly_detection_service import (
    detect_anomalies,
    list_anomalies,
    update_anomaly_status,
    batch_update_anomaly_status,
)


def _seed_batch(db: Session, name: str = "test-batch") -> ImportBatch:
    batch = ImportBatch(batch_name=name)
    db.add(batch)
    db.flush()
    return batch


def _seed_source_file(db: Session, batch: ImportBatch) -> SourceFile:
    sf = SourceFile(batch_id=batch.id, file_name="test.xlsx", file_size=1024, file_path="/tmp/test.xlsx")
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
    payment_base: Decimal | None = None,
    pension_company: Decimal | None = None,
    pension_personal: Decimal | None = None,
    unemployment_company: Decimal | None = None,
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
        payment_base=payment_base,
        pension_company=pension_company,
        pension_personal=pension_personal,
        unemployment_company=unemployment_company,
        source_file_name="test.xlsx",
    )
    db.add(rec)
    db.flush()
    return rec


class TestAnomalyRecordModel:
    """Test AnomalyRecord model creation."""

    def test_create_anomaly_record(self, db_session: Session):
        """AnomalyRecord should persist with all required fields."""
        record = AnomalyRecord(
            employee_identifier="ID001",
            person_name="Alice",
            company_name="TestCo",
            region="shenzhen",
            left_period="202601",
            right_period="202602",
            field_name="payment_base",
            left_value=Decimal("5000.00"),
            right_value=Decimal("8000.00"),
            change_percent=60.0,
            threshold_percent=15.0,
            status="pending",
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        assert record.id is not None
        assert record.employee_identifier == "ID001"
        assert record.left_period == "202601"
        assert record.right_period == "202602"
        assert record.field_name == "payment_base"
        assert record.left_value == Decimal("5000.00")
        assert record.right_value == Decimal("8000.00")
        assert record.change_percent == 60.0
        assert record.threshold_percent == 15.0
        assert record.status == "pending"


class TestDetectAnomalies:
    """Test detect_anomalies function."""

    def test_flags_payment_base_exceeding_threshold(self, db_session: Session):
        """Payment base change exceeding 15% threshold should be flagged."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        # 5000 -> 8000 = 60% change > 15% threshold
        _seed_record(db_session, batch, sf, person_name="Alice", id_number="ID001",
                      billing_period="202601", payment_base=Decimal("5000.00"))
        _seed_record(db_session, batch, sf, person_name="Alice", id_number="ID001",
                      billing_period="202602", payment_base=Decimal("8000.00"), source_row_number=2)
        db_session.commit()

        anomalies = detect_anomalies(db_session, "202601", "202602")
        payment_base_anomalies = [a for a in anomalies if a.field_name == "payment_base"]
        assert len(payment_base_anomalies) == 1
        anomaly = payment_base_anomalies[0]
        assert anomaly.status == "pending"
        assert anomaly.change_percent == 60.0
        assert anomaly.threshold_percent == 15.0

    def test_respects_pension_threshold(self, db_session: Session):
        """Pension change at exactly 20% should NOT be flagged (<=threshold)."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        # 1000 -> 1200 = 20% change == 20% threshold
        _seed_record(db_session, batch, sf, person_name="Bob", id_number="ID002",
                      billing_period="202601", pension_company=Decimal("1000.00"))
        _seed_record(db_session, batch, sf, person_name="Bob", id_number="ID002",
                      billing_period="202602", pension_company=Decimal("1200.00"), source_row_number=2)
        db_session.commit()

        anomalies = detect_anomalies(db_session, "202601", "202602")
        pension_anomalies = [a for a in anomalies if a.field_name == "pension_company"]
        assert len(pension_anomalies) == 0

    def test_flags_pension_above_threshold(self, db_session: Session):
        """Pension change above 20% threshold should be flagged."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        # 1000 -> 1250 = 25% change > 20% threshold
        _seed_record(db_session, batch, sf, person_name="Carol", id_number="ID003",
                      billing_period="202601", pension_company=Decimal("1000.00"))
        _seed_record(db_session, batch, sf, person_name="Carol", id_number="ID003",
                      billing_period="202602", pension_company=Decimal("1250.00"), source_row_number=2)
        db_session.commit()

        anomalies = detect_anomalies(db_session, "202601", "202602")
        pension_anomalies = [a for a in anomalies if a.field_name == "pension_company"]
        assert len(pension_anomalies) == 1
        assert pension_anomalies[0].change_percent == 25.0

    def test_respects_unemployment_threshold(self, db_session: Session):
        """Unemployment at 30% threshold: 29% should NOT be flagged."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        # 1000 -> 1290 = 29% change < 30% threshold
        _seed_record(db_session, batch, sf, person_name="Dave", id_number="ID004",
                      billing_period="202601", unemployment_company=Decimal("1000.00"))
        _seed_record(db_session, batch, sf, person_name="Dave", id_number="ID004",
                      billing_period="202602", unemployment_company=Decimal("1290.00"), source_row_number=2)
        db_session.commit()

        anomalies = detect_anomalies(db_session, "202601", "202602")
        unemployment_anomalies = [a for a in anomalies if a.field_name == "unemployment_company"]
        assert len(unemployment_anomalies) == 0

    def test_does_not_flag_below_threshold(self, db_session: Session):
        """No anomaly for changes below threshold."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        # 5000 -> 5500 = 10% change < 15% threshold for payment_base
        _seed_record(db_session, batch, sf, person_name="Eve", id_number="ID005",
                      billing_period="202601", payment_base=Decimal("5000.00"))
        _seed_record(db_session, batch, sf, person_name="Eve", id_number="ID005",
                      billing_period="202602", payment_base=Decimal("5500.00"), source_row_number=2)
        db_session.commit()

        anomalies = detect_anomalies(db_session, "202601", "202602")
        assert len(anomalies) == 0

    def test_custom_thresholds_override_defaults(self, db_session: Session):
        """Custom thresholds should override defaults."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        # 5000 -> 5500 = 10% change, with custom threshold of 5%
        _seed_record(db_session, batch, sf, person_name="Frank", id_number="ID006",
                      billing_period="202601", payment_base=Decimal("5000.00"))
        _seed_record(db_session, batch, sf, person_name="Frank", id_number="ID006",
                      billing_period="202602", payment_base=Decimal("5500.00"), source_row_number=2)
        db_session.commit()

        anomalies = detect_anomalies(db_session, "202601", "202602", thresholds={"payment_base": 5.0})
        payment_anomalies = [a for a in anomalies if a.field_name == "payment_base"]
        assert len(payment_anomalies) == 1

    def test_no_matched_employees_no_anomalies(self, db_session: Session):
        """Different employees in each period -> no anomalies."""
        batch = _seed_batch(db_session)
        sf = _seed_source_file(db_session, batch)
        _seed_record(db_session, batch, sf, person_name="X", id_number="ID100",
                      billing_period="202601", payment_base=Decimal("5000.00"))
        _seed_record(db_session, batch, sf, person_name="Y", id_number="ID200",
                      billing_period="202602", payment_base=Decimal("8000.00"), source_row_number=2)
        db_session.commit()

        anomalies = detect_anomalies(db_session, "202601", "202602")
        assert len(anomalies) == 0


class TestUpdateAnomalyStatus:
    """Test anomaly status update functions."""

    def test_update_single_status(self, db_session: Session):
        """update_anomaly_status should change status from pending to confirmed."""
        record = AnomalyRecord(
            employee_identifier="ID001",
            left_period="202601",
            right_period="202602",
            field_name="payment_base",
            left_value=Decimal("5000.00"),
            right_value=Decimal("8000.00"),
            change_percent=60.0,
            threshold_percent=15.0,
            status="pending",
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        updated = update_anomaly_status(db_session, record.id, "confirmed", "admin")
        assert updated.status == "confirmed"
        assert updated.reviewed_by == "admin"
        assert updated.reviewed_at is not None

    def test_update_to_excluded(self, db_session: Session):
        """update_anomaly_status should change status to excluded."""
        record = AnomalyRecord(
            employee_identifier="ID002",
            left_period="202601",
            right_period="202602",
            field_name="pension_company",
            change_percent=50.0,
            threshold_percent=20.0,
            status="pending",
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        updated = update_anomaly_status(db_session, record.id, "excluded", "hr_user")
        assert updated.status == "excluded"
        assert updated.reviewed_by == "hr_user"

    def test_batch_update_status(self, db_session: Session):
        """batch_update_anomaly_status should update multiple records."""
        records = []
        for i in range(3):
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

        ids = [rec.id for rec in records[:2]]
        count = batch_update_anomaly_status(db_session, ids, "confirmed", "admin")
        assert count == 2

        # Verify statuses
        db_session.expire_all()
        for rec in records[:2]:
            db_session.refresh(rec)
            assert rec.status == "confirmed"
        db_session.refresh(records[2])
        assert records[2].status == "pending"

    def test_update_nonexistent_raises(self, db_session: Session):
        """update_anomaly_status on nonexistent ID should raise ValueError."""
        with pytest.raises(ValueError, match="not found"):
            update_anomaly_status(db_session, "nonexistent-id", "confirmed", "admin")


class TestListAnomalies:
    """Test list_anomalies function."""

    def test_list_with_filters(self, db_session: Session):
        """list_anomalies should filter by status and field_name."""
        for i, (field, status) in enumerate([
            ("payment_base", "pending"),
            ("pension_company", "pending"),
            ("payment_base", "confirmed"),
        ]):
            db_session.add(AnomalyRecord(
                employee_identifier=f"ID{i}",
                left_period="202601",
                right_period="202602",
                field_name=field,
                change_percent=50.0,
                threshold_percent=15.0,
                status=status,
            ))
        db_session.commit()

        items, total = list_anomalies(db_session, status="pending")
        assert total == 2

        items, total = list_anomalies(db_session, field_name="payment_base")
        assert total == 2

        items, total = list_anomalies(db_session, status="pending", field_name="payment_base")
        assert total == 1

    def test_list_pagination(self, db_session: Session):
        """list_anomalies should paginate correctly."""
        for i in range(5):
            db_session.add(AnomalyRecord(
                employee_identifier=f"ID{i}",
                left_period="202601",
                right_period="202602",
                field_name="payment_base",
                change_percent=50.0,
                threshold_percent=15.0,
                status="pending",
            ))
        db_session.commit()

        items, total = list_anomalies(db_session, page=0, page_size=2)
        assert total == 5
        assert len(items) == 2

        items, total = list_anomalies(db_session, page=2, page_size=2)
        assert len(items) == 1
