from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    file_path: str
    file_size: int
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
