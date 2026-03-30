from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from sqlalchemy import and_

from backend.app.models import EmployeeMaster, ExportJob, ImportBatch, MatchResult, NormalizedRecord, SourceFile, ValidationIssue
from backend.app.models.enums import BatchStatus, MatchStatus
from backend.app.schemas.dashboard import DashboardOverviewRead, DashboardRecentBatchRead, DashboardTotalsRead
from backend.app.schemas.data_management import BatchQualityRead, DataQualityOverviewRead


EXPORT_STATUS_KEYS = ('pending', 'completed', 'failed')
ISSUE_SEVERITY_KEYS = ('error', 'warning', 'info')

# Configurable anomaly thresholds. Override via settings or per-region config as needed.
ANOMALY_THRESHOLDS = {
    "payment_base_min": 100,    # Below this is likely data error
    "payment_base_max": 80000,  # Above this is likely data error
}


def get_dashboard_overview(db: Session) -> DashboardOverviewRead:
    totals = DashboardTotalsRead(
        total_batches=_count_rows(db, ImportBatch),
        total_source_files=_count_rows(db, SourceFile),
        total_normalized_records=_count_rows(db, NormalizedRecord),
        total_validation_issues=_count_rows(db, ValidationIssue),
        total_match_results=_count_rows(db, MatchResult),
        total_export_jobs=_count_rows(db, ExportJob),
        active_employee_masters=db.query(func.count(EmployeeMaster.id)).filter(EmployeeMaster.active.is_(True)).scalar() or 0,
    )

    recent_batches = (
        db.query(ImportBatch)
        .order_by(ImportBatch.updated_at.desc(), ImportBatch.created_at.desc())
        .limit(5)
        .all()
    )

    return DashboardOverviewRead(
        generated_at=datetime.now(timezone.utc),
        totals=totals,
        batch_status_counts=_build_batch_status_counts(db),
        match_status_counts=_build_match_status_counts(db),
        issue_severity_counts=_build_issue_severity_counts(db),
        export_status_counts=_build_export_status_counts(db),
        recent_batches=[
            DashboardRecentBatchRead(
                batch_id=batch.id,
                batch_name=batch.batch_name,
                status=batch.status.value,
                file_count=len(batch.source_files),
                normalized_record_count=len(batch.normalized_records),
                validation_issue_count=len(batch.validation_issues),
                match_result_count=len(batch.match_results),
                export_job_count=len(batch.export_jobs),
                created_at=batch.created_at,
                updated_at=batch.updated_at,
            )
            for batch in recent_batches
        ],
    )



def _count_rows(db: Session, model) -> int:
    return db.query(func.count(model.id)).scalar() or 0



def _build_batch_status_counts(db: Session) -> dict[str, int]:
    counts = {status.value: 0 for status in BatchStatus}
    rows = db.query(ImportBatch.status, func.count(ImportBatch.id)).group_by(ImportBatch.status).all()
    for status, count in rows:
        key = status.value if hasattr(status, 'value') else str(status)
        counts[key] = count
    return counts



def _build_match_status_counts(db: Session) -> dict[str, int]:
    counts = {status.value: 0 for status in MatchStatus}
    rows = db.query(MatchResult.match_status, func.count(MatchResult.id)).group_by(MatchResult.match_status).all()
    for status, count in rows:
        key = status.value if hasattr(status, 'value') else str(status)
        counts[key] = count
    return counts



def _build_issue_severity_counts(db: Session) -> dict[str, int]:
    counts = {key: 0 for key in ISSUE_SEVERITY_KEYS}
    rows = db.query(ValidationIssue.severity, func.count(ValidationIssue.id)).group_by(ValidationIssue.severity).all()
    for severity, count in rows:
        counts[str(severity)] = count
    return counts



def _build_export_status_counts(db: Session) -> dict[str, int]:
    counts = {key: 0 for key in EXPORT_STATUS_KEYS}
    rows = db.query(ExportJob.status, func.count(ExportJob.id)).group_by(ExportJob.status).all()
    for status, count in rows:
        counts[str(status)] = count
    return counts


def _count_missing_fields(db: Session, batch_id: str) -> int:
    """Count records in batch missing critical identity fields."""
    from sqlalchemy import or_
    return (
        db.query(func.count(NormalizedRecord.id))
        .filter(
            NormalizedRecord.batch_id == batch_id,
            or_(
                NormalizedRecord.person_name.is_(None),
                NormalizedRecord.id_number.is_(None),
                NormalizedRecord.employee_id.is_(None),
            ),
        )
        .scalar()
        or 0
    )


def _count_anomalous_amounts(db: Session, batch_id: str) -> int:
    """Count records in batch with payment_base outside threshold range."""
    from sqlalchemy import or_
    return (
        db.query(func.count(NormalizedRecord.id))
        .filter(
            NormalizedRecord.batch_id == batch_id,
            NormalizedRecord.payment_base.isnot(None),
            or_(
                NormalizedRecord.payment_base < ANOMALY_THRESHOLDS["payment_base_min"],
                NormalizedRecord.payment_base > ANOMALY_THRESHOLDS["payment_base_max"],
            ),
        )
        .scalar()
        or 0
    )


def _count_duplicates_for_batch(db: Session, batch_id: str) -> int:
    """Count duplicate records within a batch.

    Primary key: id_number + billing_period (cross-batch, most reliable).
    Fallback: person_name + company_name + billing_period (for records missing id_number).
    """
    # Primary: find (id_number, billing_period) combos that appear more than once
    dupe_combos_primary = (
        db.query(
            NormalizedRecord.id_number,
            NormalizedRecord.billing_period,
        )
        .filter(
            NormalizedRecord.id_number.isnot(None),
            NormalizedRecord.billing_period.isnot(None),
        )
        .group_by(NormalizedRecord.id_number, NormalizedRecord.billing_period)
        .having(func.count(NormalizedRecord.id) > 1)
        .subquery()
    )

    primary_count = (
        db.query(func.count(NormalizedRecord.id))
        .filter(
            NormalizedRecord.batch_id == batch_id,
            NormalizedRecord.id_number.isnot(None),
            NormalizedRecord.billing_period.isnot(None),
        )
        .filter(
            and_(
                NormalizedRecord.id_number == dupe_combos_primary.c.id_number,
                NormalizedRecord.billing_period == dupe_combos_primary.c.billing_period,
            )
        )
        .scalar()
        or 0
    )

    # Fallback: for records without id_number, use person_name+company_name+billing_period
    dupe_combos_fallback = (
        db.query(
            NormalizedRecord.person_name,
            NormalizedRecord.company_name,
            NormalizedRecord.billing_period,
        )
        .filter(
            NormalizedRecord.id_number.is_(None),
            NormalizedRecord.person_name.isnot(None),
            NormalizedRecord.company_name.isnot(None),
            NormalizedRecord.billing_period.isnot(None),
        )
        .group_by(
            NormalizedRecord.person_name,
            NormalizedRecord.company_name,
            NormalizedRecord.billing_period,
        )
        .having(func.count(NormalizedRecord.id) > 1)
        .subquery()
    )

    fallback_count = (
        db.query(func.count(NormalizedRecord.id))
        .filter(
            NormalizedRecord.batch_id == batch_id,
            NormalizedRecord.id_number.is_(None),
            NormalizedRecord.person_name.isnot(None),
            NormalizedRecord.company_name.isnot(None),
            NormalizedRecord.billing_period.isnot(None),
        )
        .filter(
            and_(
                NormalizedRecord.person_name == dupe_combos_fallback.c.person_name,
                NormalizedRecord.company_name == dupe_combos_fallback.c.company_name,
                NormalizedRecord.billing_period == dupe_combos_fallback.c.billing_period,
            )
        )
        .scalar()
        or 0
    )

    return primary_count + fallback_count


def get_data_quality_overview(db: Session, limit: int = 10) -> DataQualityOverviewRead:
    """Get per-batch data quality metrics: missing fields, anomalous amounts, duplicates."""
    batches = (
        db.query(ImportBatch)
        .order_by(ImportBatch.created_at.desc())
        .limit(limit)
        .all()
    )

    total_missing = 0
    total_anomalous = 0
    total_duplicates = 0
    batch_quality_list: list[BatchQualityRead] = []

    for batch in batches:
        record_count = (
            db.query(func.count(NormalizedRecord.id))
            .filter(NormalizedRecord.batch_id == batch.id)
            .scalar()
            or 0
        )
        missing = _count_missing_fields(db, batch.id)
        anomalous = _count_anomalous_amounts(db, batch.id)
        duplicates = _count_duplicates_for_batch(db, batch.id)

        total_missing += missing
        total_anomalous += anomalous
        total_duplicates += duplicates

        batch_quality_list.append(
            BatchQualityRead(
                batch_id=batch.id,
                batch_name=batch.batch_name,
                record_count=record_count,
                missing_fields=missing,
                anomalous_amounts=anomalous,
                duplicate_records=duplicates,
            )
        )

    return DataQualityOverviewRead(
        total_missing=total_missing,
        total_anomalous=total_anomalous,
        total_duplicates=total_duplicates,
        batches=batch_quality_list,
    )
