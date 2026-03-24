from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SourceFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    file_path: str
    file_size: int
    source_kind: str
    region: str | None
    company_name: str | None
    file_hash: str | None
    uploaded_at: datetime


class ImportBatchSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    batch_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    file_count: int


class ImportBatchDetailRead(ImportBatchSummaryRead):
    source_files: list[SourceFileRead]


class DeleteImportBatchesInput(BaseModel):
    batch_ids: list[str] = Field(min_length=1)


class DeleteImportBatchesRead(BaseModel):
    deleted_count: int
    deleted_ids: list[str]
    missing_ids: list[str]


class HeaderMappingPreviewRead(BaseModel):
    raw_header: str
    raw_header_signature: str
    canonical_field: str | None
    mapping_source: str
    confidence: float | None
    candidate_fields: list[str]
    matched_rules: list[str]
    llm_attempted: bool
    llm_status: str
    rule_overrode_llm: bool


class FilteredRowPreviewRead(BaseModel):
    row_number: int
    reason: str
    first_value: str


class NormalizedPreviewRecordRead(BaseModel):
    source_row_number: int
    values: dict[str, object | None]
    unmapped_values: dict[str, object | None]
    raw_values: dict[str, object | None]
    raw_payload: dict[str, object | None]


class SourceFilePreviewRead(BaseModel):
    source_file_id: str
    file_name: str
    source_kind: str
    region: str | None
    company_name: str | None
    raw_sheet_name: str
    raw_header_signature: str
    normalized_record_count: int
    filtered_row_count: int
    unmapped_headers: list[str]
    header_mappings: list[HeaderMappingPreviewRead]
    filtered_rows: list[FilteredRowPreviewRead]
    preview_records: list[NormalizedPreviewRecordRead]


class ImportBatchPreviewRead(BaseModel):
    batch_id: str
    batch_name: str
    status: str
    source_files: list[SourceFilePreviewRead]


class ValidationIssueRead(BaseModel):
    normalized_record_id: str | None
    source_row_number: int
    issue_type: str
    severity: str
    field_name: str | None
    message: str


class SourceFileValidationRead(BaseModel):
    source_file_id: str
    file_name: str
    raw_sheet_name: str
    issue_count: int
    issues: list[ValidationIssueRead]


class BatchValidationRead(BaseModel):
    batch_id: str
    batch_name: str
    status: str
    total_issue_count: int
    source_files: list[SourceFileValidationRead]


class MatchRecordRead(BaseModel):
    normalized_record_id: str | None
    source_row_number: int
    person_name: str | None
    id_number: str | None
    employee_id: str | None
    employee_master_id: str | None
    match_status: str
    match_basis: str | None
    confidence: float | None
    candidate_employee_ids: list[str]


class SourceFileMatchRead(BaseModel):
    source_file_id: str
    file_name: str
    raw_sheet_name: str
    result_count: int
    results: list[MatchRecordRead]


class BatchMatchRead(BaseModel):
    batch_id: str
    batch_name: str
    status: str
    employee_master_available: bool
    employee_master_count: int
    blocked_reason: str | None
    total_records: int
    matched_count: int
    unmatched_count: int
    duplicate_count: int
    low_confidence_count: int
    source_files: list[SourceFileMatchRead]


class ExportArtifactRead(BaseModel):
    template_type: str
    status: str
    file_path: str | None
    error_message: str | None
    row_count: int


class BatchExportRead(BaseModel):
    batch_id: str
    batch_name: str
    status: str
    export_job_id: str | None
    export_status: str | None
    blocked_reason: str | None
    artifacts: list[ExportArtifactRead]
    completed_at: datetime | None
