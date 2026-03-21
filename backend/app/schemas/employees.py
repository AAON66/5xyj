from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class EmployeeMasterRead(BaseModel):
    id: str
    employee_id: str
    person_name: str
    id_number: str | None
    company_name: str | None
    department: str | None
    active: bool
    created_at: datetime


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
