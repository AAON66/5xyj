from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from typing import Any, Optional

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from backend.app.models import EmployeeMaster, EmployeeMasterAudit, ImportBatch, MatchResult, NormalizedRecord
from backend.app.models.enums import EmployeeAuditAction
from backend.app.schemas.employees import (
    EmployeeImportRead,
    EmployeeMasterCreateInput,
    EmployeeMasterAuditListRead,
    EmployeeMasterAuditRead,
    EmployeeMasterListRead,
    EmployeeMasterRead,
    EmployeeMasterStatusInput,
    EmployeeMasterUpdateInput,
    EmployeeSelfServiceProfileRead,
    EmployeeSelfServiceQueryInput,
    EmployeeSelfServiceRead,
    EmployeeSelfServiceRecordRead,
)


HEADER_ALIASES = {
    "employee_id": {"employee_id", "工号", "员工工号", "职工工号", "人员工号", "员工编号", "职员编号", "员工编码", "编号", "erp工号"},
    "person_name": {"person_name", "姓名", "员工姓名", "职工姓名", "人员姓名", "姓名name"},
    "id_number": {
        "id_number",
        "证件号码",
        "身份证号",
        "身份证号码",
        "证件号",
        "身份证",
        "身份证件号码",
        "身份证件号",
        "证件号码(身份证)",
        "证件/证件号码",
        "证件 / 证件号码",
    },
    "company_name": {"company_name", "公司", "公司名称", "所属公司", "主体", "主体公司", "法人公司", "所属法人公司", "归属公司", "用工主体", "法人主体"},
    "department": {"department", "部门", "部门名称", "所属部门", "组织", "组织架构", "一级部门", "二级部门", "部门/组别", "组别"},
    "active": {"active", "是否在职", "在职状态", "启用状态", "状态", "任职状态", "人员状态", "在离职状态"},
    "region": {"region", "地区", "所属地区", "城市", "所在城市", "地区名称"},
}

TRUE_VALUES = {"1", "true", "yes", "y", "是", "在职", "启用", "active"}
FALSE_VALUES = {"0", "false", "no", "n", "否", "离职", "停用", "inactive"}


@dataclass(slots=True)
class _EmployeeImportRow:
    employee_id: str
    person_name: str
    id_number: Optional[str]
    company_name: Optional[str]
    department: Optional[str]
    region: Optional[str]
    active: bool
    row_number: int


@dataclass(slots=True)
class HistoricalEmployeeIdentity:
    employee_id: str
    person_name: str
    id_number: Optional[str]
    company_name: Optional[str]
    active: bool = True
    id: Optional[str] = None


class EmployeeImportError(Exception):
    """Raised when employee master import input is invalid."""


class EmployeeMasterNotFoundError(Exception):
    """Raised when an employee master record cannot be found."""


class EmployeeMasterConflictError(Exception):
    """Raised when an employee master record would conflict with an existing employee id."""


class EmployeeMasterAuditNotFoundError(Exception):
    """Raised when an employee audit record cannot be found."""


class EmployeeDeleteBlockedError(Exception):
    """Raised when an employee master record cannot be deleted safely."""


class EmployeeSelfServiceNotFoundError(Exception):
    """Raised when no employee self-service result can be found."""


async def import_employee_master_file(db: Session, upload_file: UploadFile) -> EmployeeImportRead:
    file_name = upload_file.filename or "employee-master"
    raw_bytes = await upload_file.read()
    if not raw_bytes:
        raise EmployeeImportError("Employee master file is empty.")

    rows, parse_errors = _parse_employee_rows(file_name, raw_bytes)
    if not rows and not parse_errors:
        raise EmployeeImportError("Employee master file did not contain any usable rows.")

    employee_ids = [row.employee_id for row in rows]
    existing_records = {
        item.employee_id: item
        for item in db.query(EmployeeMaster).filter(EmployeeMaster.employee_id.in_(employee_ids)).all()
    }

    created_count = 0
    updated_count = 0
    imported_items: list[EmployeeMaster] = []
    audit_entries: list[EmployeeMasterAudit] = []
    for row in rows:
        existing = existing_records.get(row.employee_id)
        if existing is None:
            existing = EmployeeMaster(
                employee_id=row.employee_id,
                person_name=row.person_name,
                id_number=row.id_number,
                company_name=row.company_name,
                department=row.department,
                region=row.region,
                active=row.active,
            )
            db.add(existing)
            db.flush()
            existing_records[row.employee_id] = existing
            created_count += 1
            action = EmployeeAuditAction.IMPORT_CREATE
            note = f"Imported from {file_name}."
        else:
            existing.person_name = row.person_name
            existing.id_number = row.id_number
            existing.company_name = row.company_name
            existing.department = row.department
            existing.region = row.region
            existing.active = row.active
            updated_count += 1
            action = EmployeeAuditAction.IMPORT_UPDATE
            note = f"Updated from {file_name}."

        audit_entries.append(_build_audit(existing, action=action, note=note))
        imported_items.append(existing)

    db.add_all(audit_entries)
    db.commit()
    for item in imported_items:
        db.refresh(item)

    return EmployeeImportRead(
        file_name=file_name,
        total_rows=len(rows) + len(parse_errors),
        imported_count=len(rows),
        created_count=created_count,
        updated_count=updated_count,
        skipped_count=len(parse_errors),
        errors=parse_errors,
        items=[_to_employee_read(item) for item in imported_items],
    )


def create_employee_master(db: Session, payload: EmployeeMasterCreateInput) -> EmployeeMasterRead:
    employee_id = payload.employee_id.strip()
    if db.query(EmployeeMaster.id).filter(EmployeeMaster.employee_id == employee_id).first() is not None:
        raise EmployeeMasterConflictError(f"Employee master record already exists for employee_id: {employee_id}")

    employee = EmployeeMaster(
        employee_id=employee_id,
        person_name=payload.person_name.strip(),
        id_number=_nullable_text(payload.id_number),
        company_name=_nullable_text(payload.company_name),
        department=_nullable_text(payload.department),
        region=_nullable_text(payload.region),
        active=payload.active,
    )
    db.add(employee)
    db.flush()
    db.add(
        _build_audit(
            employee,
            action=EmployeeAuditAction.MANUAL_CREATE,
            note="Created from employee master add page.",
        )
    )
    db.commit()
    db.refresh(employee)
    return _to_employee_read(employee)


def list_employee_masters(
    db: Session,
    *,
    query: Optional[str] = None,
    region: Optional[str] = None,
    company_name: Optional[str] = None,
    active_only: bool = False,
    limit: Optional[int] = None,
    offset: int = 0,
) -> EmployeeMasterListRead:
    statement = db.query(EmployeeMaster)
    if region:
        statement = statement.filter(EmployeeMaster.region == region)
    if company_name:
        statement = statement.filter(EmployeeMaster.company_name == company_name)
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
    total = statement.count()
    statement = statement.order_by(EmployeeMaster.employee_id.asc())
    if offset > 0:
        statement = statement.offset(offset)
    if limit is not None:
        statement = statement.limit(limit)
    items = statement.all()
    return EmployeeMasterListRead(
        total=total,
        limit=limit,
        offset=offset,
        items=[_to_employee_read(item) for item in items],
    )


def list_employee_match_candidates(db: Session) -> list[EmployeeMaster | HistoricalEmployeeIdentity]:
    active_masters = list(
        db.query(EmployeeMaster).filter(EmployeeMaster.active.is_(True)).order_by(EmployeeMaster.employee_id.asc()).all()
    )
    active_employee_ids = {item.employee_id for item in active_masters}

    historical_candidates: list[HistoricalEmployeeIdentity] = []
    latest_audits = (
        db.query(EmployeeMasterAudit)
        .order_by(
            EmployeeMasterAudit.employee_id_snapshot.asc(),
            EmployeeMasterAudit.created_at.desc(),
            EmployeeMasterAudit.id.desc(),
        )
        .all()
    )
    seen_employee_ids: set[str] = set()
    for audit in latest_audits:
        employee_id = _clean_text(audit.employee_id_snapshot)
        if employee_id is None or employee_id in seen_employee_ids or employee_id in active_employee_ids:
            continue
        seen_employee_ids.add(employee_id)
        if audit.action == EmployeeAuditAction.DELETE:
            continue
        snapshot = audit.snapshot or {}
        person_name = _clean_text(snapshot.get('person_name'))
        if person_name is None:
            continue
        if snapshot.get('active') is False:
            continue
        historical_candidates.append(
            HistoricalEmployeeIdentity(
                employee_id=employee_id,
                person_name=person_name,
                id_number=_clean_text(snapshot.get('id_number')),
                company_name=_clean_text(snapshot.get('company_name')),
            )
        )

    return [*active_masters, *historical_candidates]


def update_employee_master(db: Session, employee_id: str, payload: EmployeeMasterUpdateInput) -> EmployeeMasterRead:
    employee = _get_employee_or_raise(db, employee_id)
    employee.person_name = payload.person_name.strip()
    employee.id_number = _nullable_text(payload.id_number)
    employee.company_name = _nullable_text(payload.company_name)
    employee.department = _nullable_text(payload.department)
    employee.region = _nullable_text(payload.region)
    employee.active = payload.active
    db.add(_build_audit(employee, action=EmployeeAuditAction.MANUAL_UPDATE, note="Updated from employee master management page."))
    db.commit()
    db.refresh(employee)
    return _to_employee_read(employee)


def update_employee_master_status(db: Session, employee_id: str, payload: EmployeeMasterStatusInput) -> EmployeeMasterRead:
    employee = _get_employee_or_raise(db, employee_id)
    employee.active = payload.active
    note = payload.note or ("Activated employee master record." if payload.active else "Disabled employee master record.")
    db.add(_build_audit(employee, action=EmployeeAuditAction.STATUS_CHANGE, note=note))
    db.commit()
    db.refresh(employee)
    return _to_employee_read(employee)


def delete_employee_master(db: Session, employee_id: str) -> None:
    employee = _get_employee_or_raise(db, employee_id)
    if employee.match_results:
        raise EmployeeDeleteBlockedError("Employee master record cannot be deleted because it already has match history.")

    db.add(_build_audit(employee, action=EmployeeAuditAction.DELETE, note="Deleted from employee master management page."))
    db.flush()
    db.delete(employee)
    db.commit()


def list_employee_master_audits(db: Session, employee_id: str) -> EmployeeMasterAuditListRead:
    employee = _get_employee_or_raise(db, employee_id)
    items = (
        db.query(EmployeeMasterAudit)
        .filter(EmployeeMasterAudit.employee_master_id == employee.id)
        .order_by(EmployeeMasterAudit.created_at.desc(), EmployeeMasterAudit.id.desc())
        .all()
    )
    return EmployeeMasterAuditListRead(total=len(items), items=[_to_audit_read(item) for item in items])


def delete_employee_master_audit(db: Session, employee_id: str, audit_id: str) -> None:
    employee = _get_employee_or_raise(db, employee_id)
    audit = (
        db.query(EmployeeMasterAudit)
        .filter(
            EmployeeMasterAudit.id == audit_id,
            EmployeeMasterAudit.employee_master_id == employee.id,
        )
        .one_or_none()
    )
    if audit is None:
        raise EmployeeMasterAuditNotFoundError(
            f"Employee master audit record was not found: employee_id={employee_id}, audit_id={audit_id}"
        )

    db.delete(audit)
    db.commit()


def lookup_employee_self_service(db: Session, payload: EmployeeSelfServiceQueryInput) -> EmployeeSelfServiceRead:
    person_name = _clean_text(payload.person_name)
    normalized_id_number = _normalize_identity_lookup(payload.id_number)
    if not person_name or not normalized_id_number:
        raise EmployeeSelfServiceNotFoundError("Employee identity did not match any records.")

    employee = (
        db.query(EmployeeMaster)
        .filter(EmployeeMaster.person_name == person_name)
        .filter(_normalized_identity_expression(EmployeeMaster.id_number) == normalized_id_number)
        .order_by(EmployeeMaster.active.desc(), EmployeeMaster.updated_at.desc())
        .first()
    )

    conditions = [
        and_(
            NormalizedRecord.person_name == person_name,
            _normalized_identity_expression(NormalizedRecord.id_number) == normalized_id_number,
        )
    ]
    if employee is not None:
        conditions.append(MatchResult.employee_master_id == employee.id)
        conditions.append(NormalizedRecord.employee_id == employee.employee_id)

    rows = (
        db.query(NormalizedRecord, ImportBatch)
        .join(ImportBatch, ImportBatch.id == NormalizedRecord.batch_id)
        .outerjoin(MatchResult, MatchResult.normalized_record_id == NormalizedRecord.id)
        .filter(or_(*conditions))
        .order_by(ImportBatch.created_at.desc(), NormalizedRecord.created_at.desc(), NormalizedRecord.source_row_number.asc())
        .all()
    )

    unique_records: list[tuple[NormalizedRecord, ImportBatch]] = []
    seen_record_ids: set[str] = set()
    for record, batch in rows:
        if record.id in seen_record_ids:
            continue
        seen_record_ids.add(record.id)
        unique_records.append((record, batch))

    if employee is None and not unique_records:
        raise EmployeeSelfServiceNotFoundError("Employee identity did not match any records.")

    profile = (
        _to_self_service_profile_from_employee(employee)
        if employee is not None
        else _to_self_service_profile_from_record(unique_records[0][0], normalized_id_number)
    )
    records = [_to_self_service_record(record, batch) for record, batch in unique_records]
    return EmployeeSelfServiceRead(
        matched_employee_master=employee is not None,
        profile=profile,
        record_count=len(records),
        records=records,
    )


def _parse_employee_rows(file_name: str, raw_bytes: bytes) -> tuple[list[_EmployeeImportRow], list[str]]:
    raw_dataframe = _load_tabular_file(file_name, raw_bytes)
    dataframe = _prepare_employee_dataframe(raw_dataframe)
    if dataframe.empty:
        return [], []

    dataframe = dataframe.where(pd.notnull(dataframe), None)
    column_map = _resolve_column_map(list(dataframe.columns))
    rows: list[_EmployeeImportRow] = []
    errors: list[str] = []

    for offset, row in enumerate(dataframe.to_dict(orient="records"), start=2):
        try:
            parsed = _parse_employee_row(row, column_map, row_number=offset)
        except EmployeeImportError as exc:
            errors.append(str(exc))
            continue
        if parsed is None:
            continue
        rows.append(parsed)

    return rows, errors


def _load_tabular_file(file_name: str, raw_bytes: bytes) -> pd.DataFrame:
    lower_name = file_name.lower()
    buffer = BytesIO(raw_bytes)
    if lower_name.endswith(".csv"):
        for encoding in ("utf-8-sig", "utf-8", "gbk"):
            buffer.seek(0)
            try:
                return pd.read_csv(buffer, dtype=object, encoding=encoding, header=None)
            except UnicodeDecodeError:
                continue
        raise EmployeeImportError("Employee master CSV could not be decoded with utf-8 or gbk.")
    if lower_name.endswith(".xlsx") or lower_name.endswith(".xlsm"):
        return pd.read_excel(buffer, dtype=object, header=None)
    raise EmployeeImportError("Employee master import only supports CSV or XLSX files.")


def _prepare_employee_dataframe(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    if raw_dataframe.empty:
        return raw_dataframe

    header_row_index = _detect_employee_header_row(raw_dataframe)
    headers = [_normalize_header_cell(value, index) for index, value in enumerate(raw_dataframe.iloc[header_row_index].tolist(), start=1)]
    dataframe = raw_dataframe.iloc[header_row_index + 1 :].copy()
    dataframe.columns = headers
    dataframe = dataframe.reset_index(drop=True)
    return dataframe


def _detect_employee_header_row(dataframe: pd.DataFrame) -> int:
    max_rows = min(len(dataframe.index), 8)
    best_index = 0
    best_score = -1
    for row_index in range(max_rows):
        row_values = [_clean_text(value) for value in dataframe.iloc[row_index].tolist()]
        score = _score_employee_header_row(row_values)
        if score > best_score:
            best_score = score
            best_index = row_index
    return best_index


def _score_employee_header_row(values: Optional[list[str]]) -> int:
    normalized = [_normalize_header(value or "") for value in values]
    score = 0
    for field_name, aliases in HEADER_ALIASES.items():
        alias_hits = sum(1 for alias in aliases if _normalize_header(alias) in normalized)
        if not alias_hits:
            continue
        if field_name in {"employee_id", "person_name"}:
            score += 6
        elif field_name in {"id_number", "company_name"}:
            score += 4
        else:
            score += 2
    return score


def _normalize_header_cell(value: object, index: int) -> str:
    cleaned = _clean_text(value)
    return cleaned or f"column_{index}"


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


def _parse_employee_row(row: dict[str, Any], column_map: dict[str, str], *, row_number: int) -> Optional[_EmployeeImportRow]:
    employee_id = _clean_text(row.get(column_map["employee_id"]))
    person_name = _clean_text(row.get(column_map["person_name"]))
    id_number = _clean_text(row.get(column_map.get("id_number", ""))) if column_map.get("id_number") else None
    company_name = _clean_text(row.get(column_map.get("company_name", ""))) if column_map.get("company_name") else None
    department = _clean_text(row.get(column_map.get("department", ""))) if column_map.get("department") else None
    region = _clean_text(row.get(column_map.get("region", ""))) if column_map.get("region") else None
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
        region=region,
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
    return (
        "".join(
            value.strip()
            .lower()
            .replace("（", "(")
            .replace("）", ")")
            .replace("：", "")
            .replace(":", "")
            .replace("/", "")
            .replace("\\", "")
            .replace("_", "")
            .split()
        )
    )


def _normalize_identity_lookup(value: object) -> Optional[str]:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    return cleaned.replace(" ", "").upper()


def _normalized_identity_expression(column):
    return func.upper(func.replace(func.coalesce(column, ""), " ", ""))


def _clean_text(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def _nullable_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _mask_id_number(value: Optional[str]) -> str:
    cleaned = _clean_text(value)
    if not cleaned:
        return ""
    if len(cleaned) <= 4:
        return "*" * len(cleaned)
    if len(cleaned) <= 8:
        return f"{cleaned[:2]}{'*' * (len(cleaned) - 4)}{cleaned[-2:]}"
    return f"{cleaned[:4]}{'*' * (len(cleaned) - 8)}{cleaned[-4:]}"


def _get_employee_or_raise(db: Session, employee_id: str) -> EmployeeMaster:
    employee = db.query(EmployeeMaster).filter(EmployeeMaster.id == employee_id).one_or_none()
    if employee is None:
        raise EmployeeMasterNotFoundError(f"Employee master record was not found: {employee_id}")
    return employee


def _build_audit(employee: EmployeeMaster, *, action: EmployeeAuditAction, note: Optional[str]) -> EmployeeMasterAudit:
    return EmployeeMasterAudit(
        employee_master_id=employee.id,
        employee_id_snapshot=employee.employee_id,
        action=action,
        note=note,
        snapshot={
            "employee_id": employee.employee_id,
            "person_name": employee.person_name,
            "id_number": employee.id_number,
            "company_name": employee.company_name,
            "department": employee.department,
            "region": employee.region,
            "active": employee.active,
        },
        created_at=datetime.now(UTC),
    )


def _to_employee_read(item: EmployeeMaster) -> EmployeeMasterRead:
    return EmployeeMasterRead(
        id=item.id,
        employee_id=item.employee_id,
        person_name=item.person_name,
        id_number=item.id_number,
        company_name=item.company_name,
        department=item.department,
        region=item.region,
        active=item.active,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _to_self_service_profile_from_employee(employee: EmployeeMaster) -> EmployeeSelfServiceProfileRead:
    return EmployeeSelfServiceProfileRead(
        employee_id=employee.employee_id,
        person_name=employee.person_name,
        masked_id_number=_mask_id_number(employee.id_number),
        company_name=employee.company_name,
        department=employee.department,
        active=employee.active,
        source="employee_master",
    )


def _to_self_service_profile_from_record(
    record: NormalizedRecord,
    normalized_id_number: str,
) -> EmployeeSelfServiceProfileRead:
    return EmployeeSelfServiceProfileRead(
        employee_id=record.employee_id,
        person_name=record.person_name or "",
        masked_id_number=_mask_id_number(record.id_number or normalized_id_number),
        company_name=record.company_name,
        department=None,
        active=None,
        source="normalized_record",
    )


def _to_self_service_record(record: NormalizedRecord, batch: ImportBatch) -> EmployeeSelfServiceRecordRead:
    return EmployeeSelfServiceRecordRead(
        normalized_record_id=record.id,
        batch_id=batch.id,
        batch_name=batch.batch_name,
        batch_status=batch.status.value,
        employee_id=record.employee_id,
        region=record.region,
        company_name=record.company_name,
        billing_period=record.billing_period,
        period_start=record.period_start,
        period_end=record.period_end,
        source_file_name=record.source_file_name,
        source_row_number=record.source_row_number,
        total_amount=record.total_amount,
        company_total_amount=record.company_total_amount,
        personal_total_amount=record.personal_total_amount,
        housing_fund_personal=record.housing_fund_personal,
        housing_fund_company=record.housing_fund_company,
        housing_fund_total=record.housing_fund_total,
        created_at=record.created_at,
    )


def _to_audit_read(item: EmployeeMasterAudit) -> EmployeeMasterAuditRead:
    return EmployeeMasterAuditRead(
        id=item.id,
        employee_master_id=item.employee_master_id,
        employee_id_snapshot=item.employee_id_snapshot,
        action=item.action.value,
        note=item.note,
        snapshot=item.snapshot,
        created_at=item.created_at,
    )
