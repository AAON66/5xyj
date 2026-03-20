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