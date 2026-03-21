from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.models import EmployeeMaster
from backend.app.schemas.employees import EmployeeImportRead, EmployeeMasterListRead, EmployeeMasterRead


HEADER_ALIASES = {
    "employee_id": {"employee_id", "工号", "员工工号", "职工工号", "人员工号"},
    "person_name": {"person_name", "姓名", "员工姓名", "职工姓名"},
    "id_number": {"id_number", "证件号码", "身份证号", "身份证号码", "证件号"},
    "company_name": {"company_name", "公司", "公司名称", "所属公司", "主体"},
    "department": {"department", "部门", "部门名称", "所属部门"},
    "active": {"active", "是否在职", "在职状态", "启用状态", "状态"},
}

TRUE_VALUES = {"1", "true", "yes", "y", "是", "在职", "启用", "active"}
FALSE_VALUES = {"0", "false", "no", "n", "否", "离职", "停用", "inactive"}


@dataclass(slots=True)
class _EmployeeImportRow:
    employee_id: str
    person_name: str
    id_number: str | None
    company_name: str | None
    department: str | None
    active: bool
    row_number: int


class EmployeeImportError(Exception):
    """Raised when employee master import input is invalid."""


async def import_employee_master_file(db: Session, upload_file: UploadFile) -> EmployeeImportRead:
    file_name = upload_file.filename or "employee-master"
    raw_bytes = await upload_file.read()
    if not raw_bytes:
        raise EmployeeImportError("Employee master file is empty.")

    rows = _parse_employee_rows(file_name, raw_bytes)
    if not rows:
        raise EmployeeImportError("Employee master file did not contain any usable rows.")

    employee_ids = [row.employee_id for row in rows]
    existing_records = {
        item.employee_id: item
        for item in db.query(EmployeeMaster).filter(EmployeeMaster.employee_id.in_(employee_ids)).all()
    }

    created_count = 0
    updated_count = 0
    imported_items: list[EmployeeMaster] = []
    for row in rows:
        existing = existing_records.get(row.employee_id)
        if existing is None:
            existing = EmployeeMaster(
                employee_id=row.employee_id,
                person_name=row.person_name,
                id_number=row.id_number,
                company_name=row.company_name,
                department=row.department,
                active=row.active,
            )
            db.add(existing)
            existing_records[row.employee_id] = existing
            created_count += 1
        else:
            existing.person_name = row.person_name
            existing.id_number = row.id_number
            existing.company_name = row.company_name
            existing.department = row.department
            existing.active = row.active
            updated_count += 1
        imported_items.append(existing)

    db.commit()
    for item in imported_items:
        db.refresh(item)

    return EmployeeImportRead(
        file_name=file_name,
        total_rows=len(rows),
        imported_count=len(rows),
        created_count=created_count,
        updated_count=updated_count,
        skipped_count=0,
        errors=[],
        items=[_to_employee_read(item) for item in imported_items],
    )


def list_employee_masters(
    db: Session,
    *,
    query: str | None = None,
    active_only: bool = False,
) -> EmployeeMasterListRead:
    statement = db.query(EmployeeMaster)
    if active_only:
        statement = statement.filter(EmployeeMaster.active.is_(True))
    if query:
        like_value = f"%{query.strip()}%"
        statement = statement.filter(
            or_(
                EmployeeMaster.employee_id.ilike(like_value),
                EmployeeMaster.person_name.ilike(like_value),
                EmployeeMaster.id_number.ilike(like_value),
                EmployeeMaster.company_name.ilike(like_value),
            )
        )
    items = statement.order_by(EmployeeMaster.employee_id.asc()).all()
    return EmployeeMasterListRead(total=len(items), items=[_to_employee_read(item) for item in items])


def _parse_employee_rows(file_name: str, raw_bytes: bytes) -> list[_EmployeeImportRow]:
    dataframe = _load_tabular_file(file_name, raw_bytes)
    if dataframe.empty:
        return []

    dataframe = dataframe.where(pd.notnull(dataframe), None)
    column_map = _resolve_column_map(list(dataframe.columns))
    rows: list[_EmployeeImportRow] = []
    errors: list[str] = []

    for offset, row in enumerate(dataframe.to_dict(orient="records"), start=2):
        parsed = _parse_employee_row(row, column_map, row_number=offset)
        if parsed is None:
            continue
        rows.append(parsed)

    if errors:
        raise EmployeeImportError("; ".join(errors))
    return rows


def _load_tabular_file(file_name: str, raw_bytes: bytes) -> pd.DataFrame:
    lower_name = file_name.lower()
    buffer = BytesIO(raw_bytes)
    if lower_name.endswith(".csv"):
        for encoding in ("utf-8-sig", "utf-8", "gbk"):
            buffer.seek(0)
            try:
                return pd.read_csv(buffer, dtype=object, encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise EmployeeImportError("Employee master CSV could not be decoded with utf-8 or gbk.")
    if lower_name.endswith(".xlsx") or lower_name.endswith(".xlsm"):
        return pd.read_excel(buffer, dtype=object)
    raise EmployeeImportError("Employee master import only supports CSV or XLSX files.")


def _resolve_column_map(columns: list[object]) -> dict[str, str]:
    normalized = {_normalize_header(str(column)): str(column) for column in columns}
    resolved: dict[str, str] = {}
    for canonical_field, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            matched = normalized.get(_normalize_header(alias))
            if matched is not None:
                resolved[canonical_field] = matched
                break

    required = {"employee_id", "person_name"}
    missing = [field for field in required if field not in resolved]
    if missing:
        raise EmployeeImportError(f"Employee master file is missing required columns: {', '.join(missing)}.")
    return resolved


def _parse_employee_row(row: dict[str, Any], column_map: dict[str, str], *, row_number: int) -> _EmployeeImportRow | None:
    employee_id = _clean_text(row.get(column_map["employee_id"]))
    person_name = _clean_text(row.get(column_map["person_name"]))
    id_number = _clean_text(row.get(column_map.get("id_number", ""))) if column_map.get("id_number") else None
    company_name = _clean_text(row.get(column_map.get("company_name", ""))) if column_map.get("company_name") else None
    department = _clean_text(row.get(column_map.get("department", ""))) if column_map.get("department") else None
    active = _parse_active_value(row.get(column_map.get("active", ""))) if column_map.get("active") else True

    if not any([employee_id, person_name, id_number, company_name, department]):
        return None
    if not employee_id or not person_name:
        raise EmployeeImportError(f"Employee master row {row_number} is missing employee_id or person_name.")

    return _EmployeeImportRow(
        employee_id=employee_id,
        person_name=person_name,
        id_number=id_number,
        company_name=company_name,
        department=department,
        active=active,
        row_number=row_number,
    )


def _parse_active_value(value: object) -> bool:
    text = _clean_text(value)
    if text is None:
        return True
    lowered = text.lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    return True


def _normalize_header(value: str) -> str:
    return "".join(value.strip().lower().replace("（", "(").replace("）", ")").split())


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def _to_employee_read(item: EmployeeMaster) -> EmployeeMasterRead:
    return EmployeeMasterRead(
        id=item.id,
        employee_id=item.employee_id,
        person_name=item.person_name,
        id_number=item.id_number,
        company_name=item.company_name,
        department=item.department,
        active=item.active,
        created_at=item.created_at,
    )
