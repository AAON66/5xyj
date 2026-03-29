from __future__ import annotations

from typing import Optional

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class EmployeeMasterRead(BaseModel):
    id: str
    employee_id: str
    person_name: str
    id_number: Optional[str]
    company_name: Optional[str]
    department: Optional[str]
    region: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime


class EmployeeMasterListRead(BaseModel):
    total: int
    limit: Optional[int] = None
    offset: int = 0
    items: list[EmployeeMasterRead]


class EmployeeMasterCreateInput(BaseModel):
    employee_id: str = Field(min_length=1, max_length=100)
    person_name: str = Field(min_length=1, max_length=255)
    id_number: Optional[str] = Field(default=None, max_length=100)
    company_name: Optional[str] = Field(default=None, max_length=255)
    department: Optional[str] = Field(default=None, max_length=255)
    region: Optional[str] = Field(default=None, max_length=50)
    active: bool = True


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
    id_number: Optional[str] = Field(default=None, max_length=100)
    company_name: Optional[str] = Field(default=None, max_length=255)
    department: Optional[str] = Field(default=None, max_length=255)
    region: Optional[str] = Field(default=None, max_length=50)
    active: bool = True


class EmployeeMasterStatusInput(BaseModel):
    active: bool
    note: Optional[str] = Field(default=None, max_length=255)


class EmployeeMasterAuditRead(BaseModel):
    id: str
    employee_master_id: Optional[str]
    employee_id_snapshot: str
    action: str
    note: Optional[str]
    snapshot: dict[str, object] | None
    created_at: datetime


class EmployeeMasterAuditListRead(BaseModel):
    total: int
    items: list[EmployeeMasterAuditRead]


class EmployeeSelfServiceQueryInput(BaseModel):
    person_name: str = Field(min_length=1, max_length=255)
    id_number: str = Field(min_length=1, max_length=100)


class EmployeeSelfServiceProfileRead(BaseModel):
    employee_id: Optional[str]
    person_name: str
    masked_id_number: str
    company_name: Optional[str]
    department: Optional[str]
    active: Optional[bool]
    source: str


class EmployeeSelfServiceRecordRead(BaseModel):
    normalized_record_id: str
    batch_id: str
    batch_name: str
    batch_status: str
    employee_id: Optional[str]
    region: Optional[str]
    company_name: Optional[str]
    billing_period: Optional[str]
    period_start: Optional[str]
    period_end: Optional[str]
    source_file_name: Optional[str]
    source_row_number: int
    total_amount: Optional[Decimal]
    company_total_amount: Optional[Decimal]
    personal_total_amount: Optional[Decimal]
    housing_fund_personal: Optional[Decimal]
    housing_fund_company: Optional[Decimal]
    housing_fund_total: Optional[Decimal]
    created_at: datetime


class EmployeeSelfServiceRead(BaseModel):
    matched_employee_master: bool
    profile: EmployeeSelfServiceProfileRead
    record_count: int
    records: list[EmployeeSelfServiceRecordRead]
