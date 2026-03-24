from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class EmployeeMasterRead(BaseModel):
    id: str
    employee_id: str
    person_name: str
    id_number: str | None
    company_name: str | None
    department: str | None
    active: bool
    created_at: datetime
    updated_at: datetime


class EmployeeMasterListRead(BaseModel):
    total: int
    items: list[EmployeeMasterRead]


class EmployeeImportRead(BaseModel):
    file_name: str
    total_rows: int
    imported_count: int
    created_count: int
    updated_count: int
    skipped_count: int
    errors: list[str]
    items: list[EmployeeMasterRead]


class EmployeeMasterUpdateInput(BaseModel):
    person_name: str = Field(min_length=1, max_length=255)
    id_number: str | None = Field(default=None, max_length=100)
    company_name: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    active: bool = True


class EmployeeMasterStatusInput(BaseModel):
    active: bool
    note: str | None = Field(default=None, max_length=255)


class EmployeeMasterAuditRead(BaseModel):
    id: str
    employee_master_id: str | None
    employee_id_snapshot: str
    action: str
    note: str | None
    snapshot: dict[str, object] | None
    created_at: datetime


class EmployeeMasterAuditListRead(BaseModel):
    total: int
    items: list[EmployeeMasterAuditRead]


class EmployeeSelfServiceQueryInput(BaseModel):
    person_name: str = Field(min_length=1, max_length=255)
    id_number: str = Field(min_length=1, max_length=100)


class EmployeeSelfServiceProfileRead(BaseModel):
    employee_id: str | None
    person_name: str
    masked_id_number: str
    company_name: str | None
    department: str | None
    active: bool | None
    source: str


class EmployeeSelfServiceRecordRead(BaseModel):
    normalized_record_id: str
    batch_id: str
    batch_name: str
    batch_status: str
    employee_id: str | None
    region: str | None
    company_name: str | None
    billing_period: str | None
    period_start: str | None
    period_end: str | None
    source_file_name: str | None
    source_row_number: int
    total_amount: Decimal | None
    company_total_amount: Decimal | None
    personal_total_amount: Decimal | None
    housing_fund_personal: Decimal | None
    housing_fund_company: Decimal | None
    housing_fund_total: Decimal | None
    created_at: datetime


class EmployeeSelfServiceRead(BaseModel):
    matched_employee_master: bool
    profile: EmployeeSelfServiceProfileRead
    record_count: int
    records: list[EmployeeSelfServiceRecordRead]
