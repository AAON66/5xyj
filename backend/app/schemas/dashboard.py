from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DashboardTotalsRead(BaseModel):
    total_batches: int
    total_source_files: int
    total_normalized_records: int
    total_validation_issues: int
    total_match_results: int
    total_export_jobs: int
    active_employee_masters: int


class DashboardRecentBatchRead(BaseModel):
    batch_id: str
    batch_name: str
    status: str
    file_count: int
    normalized_record_count: int
    validation_issue_count: int
    match_result_count: int
    export_job_count: int
    created_at: datetime
    updated_at: datetime


class DashboardOverviewRead(BaseModel):
    generated_at: datetime
    totals: DashboardTotalsRead
    batch_status_counts: dict[str, int]
    match_status_counts: dict[str, int]
    issue_severity_counts: dict[str, int]
    export_status_counts: dict[str, int]
    recent_batches: list[DashboardRecentBatchRead]
