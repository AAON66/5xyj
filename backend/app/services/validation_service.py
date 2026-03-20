from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from backend.app.models.validation_issue import ValidationIssue
from backend.app.services.normalization_service import NormalizedPreviewRecord, StandardizationResult

REQUIRED_FIELDS = ("person_name", "id_number", "billing_period")
CHINA_ID_REGEX = re.compile(r"^\d{17}[\dXx]$")
WEIGHT_FACTORS = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
CHECK_CODES = "10X98765432"
AMOUNT_TOLERANCE = Decimal("0.01")
UNKNOWN_PERIOD_KEY = "__missing_period__"


@dataclass(slots=True)
class ValidationPreviewIssue:
    source_row_number: int
    issue_type: str
    severity: str
    field_name: str | None
    message: str


@dataclass(slots=True)
class ValidationResult:
    source_file: str
    sheet_name: str
    issues: list[ValidationPreviewIssue]


def validate_standardized_result(result: StandardizationResult) -> ValidationResult:
    issues: list[ValidationPreviewIssue] = []

    for record in result.records:
        issues.extend(_validate_required_fields(record))
        issues.extend(_validate_id_number(record))
        issues.extend(_validate_amount_consistency(record))

    issues.extend(_validate_duplicate_records(result.records))

    return ValidationResult(
        source_file=result.source_file,
        sheet_name=result.sheet_name,
        issues=sorted(issues, key=lambda item: (item.source_row_number, item.issue_type, item.field_name or "")),
    )


def build_validation_issue_models(
    result: ValidationResult,
    *,
    batch_id: str,
    normalized_record_ids: dict[int, str] | None = None,
) -> list[ValidationIssue]:
    models: list[ValidationIssue] = []
    normalized_record_ids = normalized_record_ids or {}
    for issue in result.issues:
        models.append(
            ValidationIssue(
                batch_id=batch_id,
                normalized_record_id=normalized_record_ids.get(issue.source_row_number),
                issue_type=issue.issue_type,
                severity=issue.severity,
                field_name=issue.field_name,
                message=issue.message,
                resolved=False,
            )
        )
    return models


def _validate_required_fields(record: NormalizedPreviewRecord) -> list[ValidationPreviewIssue]:
    issues: list[ValidationPreviewIssue] = []
    for field_name in REQUIRED_FIELDS:
        if record.values.get(field_name) in {None, ""}:
            issues.append(
                ValidationPreviewIssue(
                    source_row_number=record.source_row_number,
                    issue_type="required_missing",
                    severity="error",
                    field_name=field_name,
                    message=f"Required field '{field_name}' is missing.",
                )
            )
    return issues


def _validate_id_number(record: NormalizedPreviewRecord) -> list[ValidationPreviewIssue]:
    value = record.values.get("id_number")
    if value in {None, ""}:
        return []
    if not isinstance(value, str):
        value = str(value)
    if not CHINA_ID_REGEX.match(value) or not _is_valid_china_id(value):
        return [
            ValidationPreviewIssue(
                source_row_number=record.source_row_number,
                issue_type="invalid_format",
                severity="error",
                field_name="id_number",
                message="ID number format is invalid.",
            )
        ]
    return []


def _validate_amount_consistency(record: NormalizedPreviewRecord) -> list[ValidationPreviewIssue]:
    company_total = record.values.get("company_total_amount")
    personal_total = record.values.get("personal_total_amount")
    total_amount = record.values.get("total_amount")
    if not all(isinstance(value, Decimal) for value in (company_total, personal_total, total_amount)):
        return []
    difference = abs((company_total + personal_total) - total_amount)
    if difference <= AMOUNT_TOLERANCE:
        return []
    return [
        ValidationPreviewIssue(
            source_row_number=record.source_row_number,
            issue_type="amount_mismatch",
            severity="error",
            field_name="total_amount",
            message=(
                "Total amount does not equal company_total_amount + personal_total_amount "
                f"(difference: {difference})."
            ),
        )
    ]


def _validate_duplicate_records(records: Iterable[NormalizedPreviewRecord]) -> list[ValidationPreviewIssue]:
    buckets: dict[tuple[str, str, str], list[NormalizedPreviewRecord]] = {}
    fallback_buckets: dict[tuple[str, str, str], list[NormalizedPreviewRecord]] = {}

    for record in records:
        period_key = _derive_period_key(record)
        id_number = record.values.get("id_number")
        person_name = record.values.get("person_name")
        company_name = record.values.get("company_name")
        if isinstance(id_number, str) and id_number:
            buckets.setdefault((id_number, period_key, "id"), []).append(record)
        elif isinstance(person_name, str) and person_name:
            fallback_buckets.setdefault((person_name, company_name or "", period_key), []).append(record)

    issues: list[ValidationPreviewIssue] = []
    for records_group in [*buckets.values(), *fallback_buckets.values()]:
        if len(records_group) < 2:
            continue
        row_numbers = ", ".join(str(item.source_row_number) for item in records_group)
        for record in records_group:
            issues.append(
                ValidationPreviewIssue(
                    source_row_number=record.source_row_number,
                    issue_type="duplicate_record",
                    severity="error",
                    field_name=None,
                    message=f"Potential duplicate normalized record detected with rows: {row_numbers}.",
                )
            )
    return issues


def _derive_period_key(record: NormalizedPreviewRecord) -> str:
    billing_period = record.values.get("billing_period")
    if isinstance(billing_period, str) and billing_period:
        return billing_period
    period_start = record.values.get("period_start")
    period_end = record.values.get("period_end")
    if isinstance(period_start, str) and period_start and isinstance(period_end, str) and period_end:
        return f"{period_start}|{period_end}"
    if isinstance(period_start, str) and period_start:
        return period_start
    if isinstance(period_end, str) and period_end:
        return period_end
    return UNKNOWN_PERIOD_KEY


def _is_valid_china_id(value: str) -> bool:
    try:
        datetime.strptime(value[6:14], "%Y%m%d")
    except ValueError:
        return False
    checksum = sum(int(number) * factor for number, factor in zip(value[:17], WEIGHT_FACTORS, strict=True))
    return CHECK_CODES[checksum % 11] == value[-1].upper()
