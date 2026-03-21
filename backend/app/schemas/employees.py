from __future__ import annotations

from datetime import datetime

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
