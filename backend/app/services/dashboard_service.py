from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models import EmployeeMaster, ExportJob, ImportBatch, MatchResult, NormalizedRecord, SourceFile, ValidationIssue
from backend.app.models.enums import BatchStatus, MatchStatus
from backend.app.schemas.dashboard import DashboardOverviewRead, DashboardRecentBatchRead, DashboardTotalsRead


EXPORT_STATUS_KEYS = ('pending', 'completed', 'failed')
ISSUE_SEVERITY_KEYS = ('error', 'warning', 'info')


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
