from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from backend.app.schemas.imports import ExportArtifactRead


class AggregateEmployeeImportRead(BaseModel):
    file_name: str
    imported_count: int
    created_count: int
    updated_count: int


class AggregateSourceFileRead(BaseModel):
    source_file_id: str
    file_name: str
    source_kind: str
    region: Optional[str]
    company_name: Optional[str]
    normalized_record_count: int
    filtered_row_count: int


class AggregateRunRead(BaseModel):
    batch_id: str
    batch_name: str
    status: str
    export_status: Optional[str]
    blocked_reason: Optional[str]
    fusion_messages: list[str] = []
    employee_master: Optional[AggregateEmployeeImportRead]
    total_issue_count: int
    matched_count: int
    unmatched_count: int
    duplicate_count: int
    low_confidence_count: int
    source_files: list[AggregateSourceFileRead]
    artifacts: list[ExportArtifactRead]
