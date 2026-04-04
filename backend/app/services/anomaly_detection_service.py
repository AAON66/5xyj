from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.anomaly_record import AnomalyRecord
from backend.app.models.normalized_record import NormalizedRecord
from backend.app.services.compare_service import (
    _build_compare_identity,
    _group_records_by_identity,
)

# Map insurance field names to default threshold config keys
INSURANCE_FIELDS: dict[str, str] = {
    "payment_base": "anomaly_threshold_payment_base",
    "pension_company": "anomaly_threshold_pension",
    "pension_personal": "anomaly_threshold_pension",
    "medical_company": "anomaly_threshold_medical",
    "medical_personal": "anomaly_threshold_medical",
    "medical_maternity_company": "anomaly_threshold_medical",
    "maternity_amount": "anomaly_threshold_maternity",
    "unemployment_company": "anomaly_threshold_unemployment",
    "unemployment_personal": "anomaly_threshold_unemployment",
    "injury_company": "anomaly_threshold_injury",
    "supplementary_medical_company": "anomaly_threshold_supplementary",
    "supplementary_pension_company": "anomaly_threshold_supplementary",
    "large_medical_personal": "anomaly_threshold_supplementary",
}


def _get_default_thresholds() -> dict[str, float]:
    """Build default thresholds from config settings."""
    settings = get_settings()
    result: dict[str, float] = {}
    for field_name, config_key in INSURANCE_FIELDS.items():
        result[field_name] = getattr(settings, config_key)
    return result


def _compute_change_percent(left_val: Optional[Decimal], right_val: Optional[Decimal]) -> Optional[float]:
    """Compute absolute percentage change between two values.

    Returns None if both are zero/None (no meaningful change).
    """
    left = float(left_val) if left_val is not None else 0.0
    right = float(right_val) if right_val is not None else 0.0

    if left == 0.0 and right == 0.0:
        return None
    if left == 0.0:
        return 100.0  # New value appeared
    return abs((right - left) / left) * 100.0


def detect_anomalies(
    db: Session,
    left_period: str,
    right_period: str,
    thresholds: Optional[dict[str, float]] = None,
) -> list[AnomalyRecord]:
    """Compare NormalizedRecords across two periods and flag anomalous changes.

    For each matched employee, compares insurance fields. If the absolute
    percentage change exceeds the threshold, creates an AnomalyRecord with
    status='pending'.
    """
    effective_thresholds = _get_default_thresholds()
    if thresholds:
        effective_thresholds.update(thresholds)

    # Delete existing anomaly records for this period pair (idempotent re-run)
    db.query(AnomalyRecord).filter(
        AnomalyRecord.left_period == left_period,
        AnomalyRecord.right_period == right_period,
    ).delete(synchronize_session="fetch")

    left_records = db.query(NormalizedRecord).filter(
        NormalizedRecord.billing_period == left_period
    ).all()
    right_records = db.query(NormalizedRecord).filter(
        NormalizedRecord.billing_period == right_period
    ).all()

    left_groups = _group_records_by_identity(left_records)
    right_groups = _group_records_by_identity(right_records)

    common_keys = set(left_groups.keys()) & set(right_groups.keys())
    created: list[AnomalyRecord] = []

    for identity in common_keys:
        left_list = left_groups[identity]
        right_list = right_groups[identity]
        # Use the first record from each period for comparison
        left_rec = left_list[0]
        right_rec = right_list[0]

        employee_id = identity.value

        for field_name, config_key in INSURANCE_FIELDS.items():
            threshold = effective_thresholds.get(field_name)
            if threshold is None:
                continue

            left_val = getattr(left_rec, field_name, None)
            right_val = getattr(right_rec, field_name, None)
            change_pct = _compute_change_percent(left_val, right_val)

            if change_pct is None:
                continue
            if change_pct <= threshold:
                continue

            record = AnomalyRecord(
                employee_identifier=employee_id,
                person_name=right_rec.person_name or left_rec.person_name,
                company_name=right_rec.company_name or left_rec.company_name,
                region=right_rec.region or left_rec.region,
                left_period=left_period,
                right_period=right_period,
                field_name=field_name,
                left_value=left_val,
                right_value=right_val,
                change_percent=round(change_pct, 2),
                threshold_percent=threshold,
                status="pending",
            )
            db.add(record)
            created.append(record)

    if created:
        db.commit()
        for rec in created:
            db.refresh(rec)

    return created


def list_anomalies(
    db: Session,
    *,
    left_period: Optional[str] = None,
    right_period: Optional[str] = None,
    status: Optional[str] = None,
    field_name: Optional[str] = None,
    page: int = 0,
    page_size: int = 20,
) -> tuple[list[AnomalyRecord], int]:
    """Query anomaly records with optional filters and pagination."""
    query = db.query(AnomalyRecord)

    if left_period is not None:
        query = query.filter(AnomalyRecord.left_period == left_period)
    if right_period is not None:
        query = query.filter(AnomalyRecord.right_period == right_period)
    if status is not None:
        query = query.filter(AnomalyRecord.status == status)
    if field_name is not None:
        query = query.filter(AnomalyRecord.field_name == field_name)

    total = query.count()
    items = query.order_by(AnomalyRecord.created_at.desc()).offset(page * page_size).limit(page_size).all()
    return items, total


def update_anomaly_status(
    db: Session,
    anomaly_id: str,
    status: str,
    reviewed_by: str,
) -> AnomalyRecord:
    """Update a single anomaly record status."""
    record = db.query(AnomalyRecord).filter(AnomalyRecord.id == anomaly_id).first()
    if record is None:
        raise ValueError(f"Anomaly record '{anomaly_id}' not found")

    record.status = status
    record.reviewed_by = reviewed_by
    record.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return record


def batch_update_anomaly_status(
    db: Session,
    anomaly_ids: list[str],
    status: str,
    reviewed_by: str,
) -> int:
    """Batch update anomaly record statuses. Returns count of updated records."""
    now = datetime.now(timezone.utc)
    count = (
        db.query(AnomalyRecord)
        .filter(AnomalyRecord.id.in_(anomaly_ids))
        .update(
            {
                AnomalyRecord.status: status,
                AnomalyRecord.reviewed_by: reviewed_by,
                AnomalyRecord.reviewed_at: now,
            },
            synchronize_session="fetch",
        )
    )
    db.commit()
    return count
