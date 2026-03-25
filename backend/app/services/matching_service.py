from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Optional

from backend.app.models.employee_master import EmployeeMaster
from backend.app.models.enums import MatchStatus
from backend.app.models.match_result import MatchResult
from backend.app.models.normalized_record import NormalizedRecord
from backend.app.services.normalization_service import NormalizedPreviewRecord

HEADER_LIKE_IDENTITY_VALUES = {
    '姓名',
    '身份证号',
    '身份证号码',
    '证件号',
    '证件号码',
    '工号',
    '员工姓名',
    '员工工号',
}
ID_NUMBER_PATTERN = re.compile(r'^\d{15}$|^\d{17}[\dX]$')
NON_MAINLAND_ID_NUMBER_PATTERN = re.compile(r'^[A-Z]{1,2}\d{6,10}[A-Z0-9]?$')


@dataclass(slots=True)
class MatchPreviewResult:
    source_row_number: int
    match_status: str
    employee_id: Optional[str]
    employee_master_id: Optional[str]
    match_basis: Optional[str]
    confidence: Optional[float]
    candidate_employee_ids: list[str]


def match_preview_records(
    records: Iterable[NormalizedPreviewRecord],
    employee_masters: Iterable[EmployeeMaster],
) -> list[MatchPreviewResult]:
    employees = [employee for employee in employee_masters if employee.active]
    return [_match_preview_record(record, employees) for record in records]


def build_match_result_models(
    results: Iterable[MatchPreviewResult],
    *,
    batch_id: str,
    normalized_record_ids: dict[int, str],
    employee_master_ids: dict[str, str] | None = None,
) -> list[MatchResult]:
    employee_master_ids = employee_master_ids or {}
    models: list[MatchResult] = []
    for result in results:
        normalized_record_id = normalized_record_ids[result.source_row_number]
        employee_master_id = result.employee_master_id
        if employee_master_id is None and result.employee_id is not None:
            employee_master_id = employee_master_ids.get(result.employee_id)
        models.append(
            MatchResult(
                batch_id=batch_id,
                normalized_record_id=normalized_record_id,
                employee_master_id=employee_master_id,
                match_status=MatchStatus(result.match_status),
                match_basis=result.match_basis,
                confidence=result.confidence,
            )
        )
    return models


def apply_match_results_to_normalized_records(
    records: Iterable[NormalizedRecord],
    results: Iterable[MatchPreviewResult],
) -> None:
    indexed_results = {result.source_row_number: result for result in results}
    for record in records:
        result = indexed_results.get(record.source_row_number)
        if result is None:
            continue
        if result.employee_id and result.match_status in {
            MatchStatus.MATCHED.value,
            MatchStatus.LOW_CONFIDENCE.value,
        }:
            record.employee_id = result.employee_id


def _match_preview_record(record: NormalizedPreviewRecord, employees: list[EmployeeMaster]) -> MatchPreviewResult:
    values = record.values
    raw_id_number = values.get('id_number')
    id_number = _normalize_id_number(values.get('id_number'))
    person_name = _normalize(values.get('person_name'))
    company_name = _normalize(values.get('company_name'))
    can_fallback_without_id = _is_missing_id_number(raw_id_number)

    if id_number:
        exact_matches = [employee for employee in employees if _normalize_id_number(employee.id_number) == id_number]
        exact_result = _resolve_candidates(
            record.source_row_number,
            exact_matches,
            match_status=MatchStatus.MATCHED.value,
            match_basis='id_number_exact',
            confidence=1.0,
        )
        if exact_result is not None:
            return exact_result

    if person_name and company_name and can_fallback_without_id:
        company_matches = [
            employee
            for employee in employees
            if _normalize(employee.person_name) == person_name and _normalize(employee.company_name) == company_name
        ]
        company_result = _resolve_candidates(
            record.source_row_number,
            company_matches,
            match_status=MatchStatus.MATCHED.value,
            match_basis='person_name_company_exact',
            confidence=0.9,
        )
        if company_result is not None:
            return company_result

    if person_name and can_fallback_without_id:
        name_matches = [employee for employee in employees if _normalize(employee.person_name) == person_name]
        name_result = _resolve_candidates(
            record.source_row_number,
            name_matches,
            match_status=MatchStatus.LOW_CONFIDENCE.value,
            match_basis='person_name_exact',
            confidence=0.6,
        )
        if name_result is not None:
            return name_result

    return MatchPreviewResult(
        source_row_number=record.source_row_number,
        match_status=MatchStatus.UNMATCHED.value,
        employee_id=None,
        employee_master_id=None,
        match_basis=None,
        confidence=None,
        candidate_employee_ids=[],
    )


def _resolve_candidates(
    source_row_number: int,
    matches: list[EmployeeMaster],
    *,
    match_status: str,
    match_basis: str,
    confidence: float,
) -> Optional[MatchPreviewResult]:
    if not matches:
        return None
    if len(matches) > 1:
        return MatchPreviewResult(
            source_row_number=source_row_number,
            match_status=MatchStatus.DUPLICATE.value,
            employee_id=None,
            employee_master_id=None,
            match_basis=f'{match_basis}_duplicate',
            confidence=None,
            candidate_employee_ids=[employee.employee_id for employee in matches],
        )
    matched_employee = matches[0]
    return MatchPreviewResult(
        source_row_number=source_row_number,
        match_status=match_status,
        employee_id=matched_employee.employee_id,
        employee_master_id=matched_employee.id,
        match_basis=match_basis,
        confidence=confidence,
        candidate_employee_ids=[matched_employee.employee_id],
    )


def _normalize(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_id_number(value: object) -> Optional[str]:
    text = _normalize(value)
    if text is None:
        return None
    compact = text.replace(' ', '').upper()
    if compact in HEADER_LIKE_IDENTITY_VALUES:
        return None
    if ID_NUMBER_PATTERN.fullmatch(compact):
        return compact
    if NON_MAINLAND_ID_NUMBER_PATTERN.fullmatch(compact):
        return compact
    return None


def _is_missing_id_number(value: object) -> bool:
    text = _normalize(value)
    if text is None:
        return True
    compact = text.replace(' ', '').upper()
    return compact in HEADER_LIKE_IDENTITY_VALUES
