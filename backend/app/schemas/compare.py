from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CompareBatchMetaRead(BaseModel):
    id: str
    batch_name: str
    status: str
    record_count: int


class CompareRecordSideRead(BaseModel):
    record_id: Optional[str]
    source_file_id: Optional[str]
    source_file_name: Optional[str]
    source_row_number: Optional[int]
    values: dict[str, object | None]


class CompareRowRead(BaseModel):
    compare_key: str
    match_basis: str
    diff_status: str
    different_fields: list[str]
    left: CompareRecordSideRead
    right: CompareRecordSideRead


class BatchCompareRead(BaseModel):
    left_batch: CompareBatchMetaRead
    right_batch: CompareBatchMetaRead
    fields: list[str]
    total_row_count: int
    same_row_count: int
    changed_row_count: int
    left_only_count: int
    right_only_count: int
    rows: list[CompareRowRead]


class CompareRecordSideInput(BaseModel):
    record_id: Optional[str] = None
    source_file_id: Optional[str] = None
    source_file_name: Optional[str] = None
    source_row_number: Optional[int] = None
    values: dict[str, object | None] = {}


class CompareRowInput(BaseModel):
    compare_key: str
    match_basis: str
    diff_status: str
    different_fields: list[str] = []
    left: CompareRecordSideInput
    right: CompareRecordSideInput


class CompareExportRequest(BaseModel):
    left_batch_name: str
    right_batch_name: str
    fields: list[str]
    rows: list[CompareRowInput]


class PeriodCompareSummaryGroup(BaseModel):
    company_name: Optional[str] = None
    region: Optional[str] = None
    total_count: int = 0
    changed_count: int = 0
    left_only_count: int = 0
    right_only_count: int = 0
    same_count: int = 0


class PeriodCompareRead(BaseModel):
    left_period: str
    right_period: str
    fields: list[str]
    total_row_count: int
    same_row_count: int
    changed_row_count: int
    left_only_count: int
    right_only_count: int
    rows: list[CompareRowRead]
    summary_groups: list[PeriodCompareSummaryGroup] = []
