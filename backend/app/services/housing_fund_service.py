from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Optional

from backend.app.parsers.workbook_loader import load_workbook_compatible
from backend.app.services.header_normalizer import HeaderMappingDecision, HeaderNormalizationResult
from backend.app.services.normalization_service import NormalizedPreviewRecord, StandardizationResult
from backend.app.utils.period_utils import (
    coalesce_billing_period,
    infer_billing_period_from_filename,
    normalize_billing_period,
)

HEADER_PATTERNS: dict[str, tuple[str, ...]] = {
    "person_name": ("\u59d3\u540d", "\u804c\u5de5\u59d3\u540d"),
    "id_number": ("\u8bc1\u4ef6\u53f7\u7801",),
    "id_type": ("\u8bc1\u4ef6\u7c7b\u578b",),
    "company_name": ("\u5355\u4f4d\u540d\u79f0", "\u7528\u5de5\u5355\u4f4d\u540d\u79f0"),
    "billing_period": ("\u7f34\u5b58\u65f6\u6bb5", "\u4e1a\u52a1\u5e74\u6708", "\u6c47\u8865\u7f34\u5e74\u6708", "\u6c47\u7f34\u5e74\u6708"),
    "housing_fund_account": ("\u516c\u79ef\u91d1\u8d26\u53f7", "\u4e2a\u4eba\u516c\u79ef\u91d1\u8d26\u53f7", "\u4e2a\u4eba\u8d26\u53f7", "\u4e2a\u4eba\u5ba2\u6237\u53f7", "\u804c\u5de5\u8d26\u53f7"),
    "housing_fund_base": ("\u7f34\u5b58\u57fa\u6570", "\u7f34\u5b58\u57fa\u6570\uff08\u5143\uff09", "\u6708\u5747\u5de5\u8d44"),
    "housing_fund_personal": ("\u4e2a\u4eba\u7f34\u5b58\u989d", "\u4e2a\u4eba\u6708\u7f34\u5b58\u989d(\u5143)", "\u804c\u5de5\u6708\u7f34\u989d", "\u6708\u7f34\u5b58\u989d(\u5143)\u4e2a\u4eba", "\u5e94\u7f34\u5b58\u989d\u589e\u52a0\u4e2a\u4eba", "\u5e94\u7f34\u5b58\u989d\u51cf\u5c11\u4e2a\u4eba"),
    "housing_fund_company": ("\u5355\u4f4d\u7f34\u5b58\u989d", "\u5355\u4f4d\u6708\u7f34\u5b58\u989d(\u5143)", "\u5355\u4f4d\u6708\u7f34\u989d", "\u6708\u7f34\u5b58\u989d(\u5143)\u5355\u4f4d", "\u5e94\u7f34\u5b58\u989d\u589e\u52a0\u5355\u4f4d", "\u5e94\u7f34\u5b58\u989d\u51cf\u5c11\u5355\u4f4d"),
    "housing_fund_total": ("\u91d1\u989d\u5408\u8ba1\uff08\u5143\uff09", "\u5408\u8ba1\u6708\u7f34\u5b58\u989d(\u5143)", "\u6708\u7f34\u5b58\u989d(\u5143)\u5408\u8ba1", "\u603b\u91d1\u989d", "\u53d1\u751f\u989d", "\u5e94\u7f34\u5b58\u989d\u589e\u52a0\u5408\u8ba1", "\u5e94\u7f34\u5b58\u989d\u51cf\u5c11\u5408\u8ba1"),
}
RATE_PATTERNS: dict[str, tuple[str, ...]] = {
    "company_rate": ("\u5355\u4f4d\u7f34\u5b58\u6bd4\u4f8b",),
    "personal_rate": ("\u4e2a\u4eba\u7f34\u5b58\u6bd4\u4f8b",),
}
PLACEHOLDER_STRINGS = {"", "-", "--", "\u2014\u2014", "none", "null", "(\u7a7a\u767d)"}
NON_DETAIL_NAME_PATTERNS = ("经办网点", "打印日期", "管理中心", "制表人", "说明", "备注", "汇总", "合计")


@dataclass
class HousingFundWorkbookAnalysis:
    normalization: HeaderNormalizationResult
    standardized: StandardizationResult


@dataclass
class _WorkbookCandidate:
    sheet_name: str
    header_row: int
    data_start_row: int
    headers: list[str]
    raw_header_signature: str


def analyze_housing_fund_workbook(
    path: str | Path,
    *,
    region: Optional[str] = None,
    company_name: Optional[str] = None,
    source_file_name: Optional[str] = None,
) -> HousingFundWorkbookAnalysis:
    workbook_path = Path(path)
    workbook = load_workbook_compatible(workbook_path, read_only=True, data_only=True)
    try:
        candidate = _detect_workbook_candidate(workbook, workbook_path.name)
        sheet = workbook[candidate.sheet_name]
        workbook_company_name = company_name or _extract_company_name(sheet, candidate.header_row)
        decisions = [_build_decision(header) for header in candidate.headers]
        normalization = HeaderNormalizationResult(
            source_file=source_file_name or workbook_path.name,
            sheet_name=candidate.sheet_name,
            raw_header_signature=candidate.raw_header_signature,
            decisions=decisions,
            unmapped_headers=[decision.raw_header_signature for decision in decisions if decision.canonical_field is None],
        )

        records: list[NormalizedPreviewRecord] = []
        row_number = candidate.data_start_row
        while row_number <= sheet.max_row:
            row_values = [sheet.cell(row_number, index + 1).value for index in range(len(candidate.headers))]
            row_values = _align_row_values(candidate.headers, row_values)
            preview = _build_preview_record(
                headers=candidate.headers,
                values=row_values,
                source_file_name=source_file_name or workbook_path.name,
                sheet_name=candidate.sheet_name,
                raw_header_signature=candidate.raw_header_signature,
                row_number=row_number,
                region=region,
                company_name=workbook_company_name,
            )
            if preview is not None:
                records.append(preview)
            row_number += 1

        standardized = StandardizationResult(
            source_file=source_file_name or workbook_path.name,
            sheet_name=candidate.sheet_name,
            raw_header_signature=candidate.raw_header_signature,
            records=records,
            filtered_rows=[],
            unmapped_headers=normalization.unmapped_headers,
        )
        return HousingFundWorkbookAnalysis(normalization=normalization, standardized=standardized)
    finally:
        workbook.close()


def standardize_housing_fund_workbook(
    path: str | Path,
    *,
    region: Optional[str] = None,
    company_name: Optional[str] = None,
    source_file_name: Optional[str] = None,
) -> StandardizationResult:
    return analyze_housing_fund_workbook(
        path,
        region=region,
        company_name=company_name,
        source_file_name=source_file_name,
    ).standardized


def _detect_workbook_candidate(workbook, source_file_name: str) -> _WorkbookCandidate:
    best_candidate: Optional[_WorkbookCandidate] = None
    best_score = -1
    for sheet in workbook.worksheets:
        for row_number in range(1, min(sheet.max_row, 12) + 1):
            primary_headers = _read_row_texts(sheet, row_number)
            candidate_options: Optional[list[tuple[list[str]], int]] = [(primary_headers, row_number + 1)]
            if row_number < sheet.max_row:
                secondary_headers = _read_row_texts(sheet, row_number + 1)
                candidate_options.append((_compose_headers(primary_headers, secondary_headers), row_number + 2))

            for headers, data_start_row in candidate_options:
                score = _score_headers(headers)
                if score <= best_score:
                    continue
                best_score = score
                filtered_headers = [header or f"column_{index + 1}" for index, header in enumerate(headers)]
                best_candidate = _WorkbookCandidate(
                    sheet_name=sheet.title,
                    header_row=row_number,
                    data_start_row=data_start_row,
                    headers=filtered_headers,
                    raw_header_signature=" | ".join(filtered_headers),
                )

    if best_candidate is None or best_score < 8:
        raise ValueError(f"Could not detect a valid housing fund header row in {source_file_name}.")
    return best_candidate


def _compose_headers(primary_headers: Optional[list[str]], secondary_headers: Optional[list[str]]) -> Optional[list[str]]:
    composed: Optional[list[str]] = []
    current_primary: Optional[str] = None
    max_length = max(len(primary_headers), len(secondary_headers))

    for index in range(max_length):
        primary = primary_headers[index] if index < len(primary_headers) else None
        secondary = secondary_headers[index] if index < len(secondary_headers) else None

        if primary:
            current_primary = primary

        inherited_primary = current_primary if secondary else primary
        if inherited_primary and secondary:
            composed.append(f"{inherited_primary} {secondary}")
        else:
            composed.append(secondary or inherited_primary)

    return composed


def _score_headers(headers: Optional[list[str]]) -> int:
    score = 0
    normalized = [item or "" for item in headers]
    if any(_header_matches(header, HEADER_PATTERNS["person_name"]) for header in normalized):
        score += 4
    if any(_header_matches(header, HEADER_PATTERNS["id_number"]) for header in normalized):
        score += 4
    if any(_header_matches(header, HEADER_PATTERNS["housing_fund_account"]) for header in normalized):
        score += 3
    if any(_header_matches(header, HEADER_PATTERNS["housing_fund_total"]) for header in normalized):
        score += 3
    if any(_header_matches(header, HEADER_PATTERNS["housing_fund_personal"]) for header in normalized):
        score += 2
    if any(_header_matches(header, HEADER_PATTERNS["housing_fund_company"]) for header in normalized):
        score += 2
    if any(_header_matches(header, HEADER_PATTERNS["housing_fund_base"]) for header in normalized):
        score += 1
    return score


def _build_decision(header: str) -> HeaderMappingDecision:
    canonical_field = None
    for field_name, patterns in HEADER_PATTERNS.items():
        if _header_matches(header, patterns):
            canonical_field = field_name
            break
    return HeaderMappingDecision(
        raw_header=header,
        raw_header_signature=header,
        canonical_field=canonical_field,
        mapping_source="rule" if canonical_field else "unmapped",
        confidence=0.98 if canonical_field else None,
        candidate_fields=[canonical_field] if canonical_field else [],
        matched_rules=[header] if canonical_field else [],
    )


def _extract_company_name(sheet, header_row: int) -> Optional[str]:
    for row_number in range(1, min(header_row, 6) + 1):
        values = _read_row_texts(sheet, row_number)
        for index, value in enumerate(values):
            if not value:
                continue
            if "\u5355\u4f4d\u540d\u79f0" in value and "\uff1a" in value:
                return value.split("\uff1a", 1)[-1].strip() or None
            if value == "\u5355\u4f4d\u540d\u79f0\uff1a" and index + 1 < len(values):
                neighbor = values[index + 1]
                if neighbor:
                    return neighbor
    return None


def _build_preview_record(
    *,
    headers: list[str],
    values: list[object],
    source_file_name: str,
    sheet_name: str,
    raw_header_signature: str,
    row_number: int,
    region: Optional[str],
    company_name: Optional[str],
) -> Optional[NormalizedPreviewRecord]:
    raw_values = {header: _clean_cell_value(value) for header, value in zip(headers, values, strict=True)}
    person_name = _find_first_value(raw_values, HEADER_PATTERNS["person_name"])
    id_number = _find_first_value(raw_values, HEADER_PATTERNS["id_number"])
    if not person_name and not id_number:
        return None
    if _looks_like_non_detail_record(person_name, id_number):
        return None

    raw_period_value = _find_first_value(raw_values, HEADER_PATTERNS["billing_period"])
    billing_period = coalesce_billing_period(
        raw_period_value,
        raw_header_signature,
        infer_billing_period_from_filename(source_file_name),
    )
    period_start, period_end = _derive_period_bounds(raw_period_value, fallback=billing_period)
    housing_account = _find_first_value(raw_values, HEADER_PATTERNS["housing_fund_account"])
    housing_base = _to_decimal(_find_first_value(raw_values, HEADER_PATTERNS["housing_fund_base"]))
    personal_amount = _to_decimal(_find_first_value(raw_values, HEADER_PATTERNS["housing_fund_personal"]))
    company_amount = _to_decimal(_find_first_value(raw_values, HEADER_PATTERNS["housing_fund_company"]))
    total_amount = _to_decimal(_find_first_value(raw_values, HEADER_PATTERNS["housing_fund_total"]))
    personal_rate = _to_decimal(_find_first_value(raw_values, RATE_PATTERNS["personal_rate"]))
    company_rate = _to_decimal(_find_first_value(raw_values, RATE_PATTERNS["company_rate"]))

    inference_notes: list[str] = []
    personal_amount, company_amount, total_amount = _resolve_housing_amounts(
        personal_amount=personal_amount,
        company_amount=company_amount,
        total_amount=total_amount,
        base_amount=housing_base,
        personal_rate=personal_rate,
        company_rate=company_rate,
        inference_notes=inference_notes,
    )

    record_company_name = _find_first_value(raw_values, HEADER_PATTERNS["company_name"]) or company_name
    raw_payload = {
        "raw_values": {key: _json_safe(value) for key, value in raw_values.items()},
        "unmapped_values": {},
    }
    if inference_notes:
        raw_payload["housing_fund_inference_notes"] = inference_notes

    values_payload: dict[str, Any] = {
        "person_name": person_name,
        "id_number": id_number,
        "id_type": _find_first_value(raw_values, HEADER_PATTERNS["id_type"]),
        "company_name": record_company_name,
        "region": region,
        "billing_period": billing_period,
        "period_start": period_start,
        "period_end": period_end,
        "housing_fund_account": housing_account,
        "housing_fund_base": housing_base,
        "housing_fund_personal": personal_amount,
        "housing_fund_company": company_amount,
        "housing_fund_total": total_amount,
        "raw_sheet_name": sheet_name,
        "raw_header_signature": raw_header_signature,
        "source_file_name": source_file_name,
    }
    return NormalizedPreviewRecord(
        source_row_number=row_number,
        values={key: value for key, value in values_payload.items() if value is not None},
        unmapped_values={},
        raw_values=raw_values,
        raw_payload=raw_payload,
    )


def _looks_like_non_detail_record(person_name: Optional[str], id_number: Optional[str]) -> bool:
    normalized_name = str(person_name or '').replace(' ', '')
    normalized_id = str(id_number or '').strip()
    if any(pattern in normalized_name for pattern in NON_DETAIL_NAME_PATTERNS):
        return True
    if normalized_name and len(normalized_name) > 20 and not normalized_id:
        return True
    return False


def _resolve_housing_amounts(
    *,
    personal_amount: Optional[Decimal],
    company_amount: Optional[Decimal],
    total_amount: Optional[Decimal],
    base_amount: Optional[Decimal],
    personal_rate: Optional[Decimal],
    company_rate: Optional[Decimal],
    inference_notes: list[str],
) -> Optional[tuple[Decimal], Decimal | None, Decimal | None]:
    quant = Decimal("0.01")

    if total_amount is None and personal_amount is not None and company_amount is not None:
        total_amount = (personal_amount + company_amount).quantize(quant)

    if personal_amount is None and company_amount is None and total_amount is not None:
        if base_amount is not None and personal_rate is not None and company_rate is not None and (personal_rate + company_rate) != 0:
            total_rate = personal_rate + company_rate
            personal_amount = (total_amount * personal_rate / total_rate).quantize(quant, rounding=ROUND_HALF_UP)
            company_amount = (total_amount - personal_amount).quantize(quant, rounding=ROUND_HALF_UP)
            inference_notes.append("split_from_total_and_rates")
        else:
            personal_amount = (total_amount / Decimal("2")).quantize(quant, rounding=ROUND_HALF_UP)
            company_amount = (total_amount - personal_amount).quantize(quant, rounding=ROUND_HALF_UP)
            inference_notes.append("split_equally_from_total")

    if personal_amount is None and total_amount is not None and company_amount is not None:
        personal_amount = (total_amount - company_amount).quantize(quant, rounding=ROUND_HALF_UP)
        inference_notes.append("derived_personal_from_total")
    if company_amount is None and total_amount is not None and personal_amount is not None:
        company_amount = (total_amount - personal_amount).quantize(quant, rounding=ROUND_HALF_UP)
        inference_notes.append("derived_company_from_total")

    if personal_amount is None and base_amount is not None and personal_rate is not None:
        personal_amount = (base_amount * personal_rate).quantize(quant, rounding=ROUND_HALF_UP)
        inference_notes.append("derived_personal_from_base_rate")
    if company_amount is None and base_amount is not None and company_rate is not None:
        company_amount = (base_amount * company_rate).quantize(quant, rounding=ROUND_HALF_UP)
        inference_notes.append("derived_company_from_base_rate")

    if total_amount is None and personal_amount is not None and company_amount is not None:
        total_amount = (personal_amount + company_amount).quantize(quant, rounding=ROUND_HALF_UP)
    return personal_amount, company_amount, total_amount


def _find_first_value(raw_values: dict[str, Any], patterns: tuple[str, ...]) -> Any:
    for header, value in raw_values.items():
        if _header_matches(header, patterns):
            return value
    return None


def _header_matches(header: Optional[str], patterns: tuple[str, ...]) -> bool:
    normalized = _normalize_header_text(header)
    return any(_normalize_header_text(pattern) in normalized for pattern in patterns)


def _normalize_period(value: Any) -> Optional[str]:
    return normalize_billing_period(value)


def _derive_period_bounds(value: Any, *, fallback: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    if value is None:
        return fallback, fallback
    text = str(value).strip()
    if not text:
        return fallback, fallback
    if "-" in text and len(text.replace("-", "")) == 12:
        start_raw, end_raw = text.split("-", 1)
        start = _normalize_period(start_raw)
        end = _normalize_period(end_raw)
        return start, end
    normalized = _normalize_period(text)
    if normalized is not None:
        return normalized, normalized
    return fallback, fallback


def _clean_text(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _read_row_texts(sheet, row_number: int) -> Optional[list[str]]:
    max_column = getattr(sheet, "max_column", 0) or 0
    if max_column <= 0:
        return []
    return [_clean_text(sheet.cell(row=row_number, column=column_index).value) for column_index in range(1, max_column + 1)]


def _normalize_header_text(value: Optional[str]) -> str:
    return (
        (value or "")
        .replace(" ", "")
        .replace("（", "(")
        .replace("）", ")")
        .replace("：", ":")
        .strip()
        .lower()
    )


def _align_row_values(headers: list[str], values: list[object]) -> list[object]:
    if not _looks_like_leading_sequence_shift(headers, values):
        return values
    return [*values[1:], None]


def _looks_like_leading_sequence_shift(headers: list[str], values: list[object]) -> bool:
    if len(headers) < 4 or len(values) < 4:
        return False
    if not _header_matches(headers[0], HEADER_PATTERNS["housing_fund_account"]):
        return False
    if not _header_matches(headers[1], HEADER_PATTERNS["person_name"]):
        return False
    if _normalize_header_text(headers[2]) != _normalize_header_text("\u6458\u8981"):
        return False
    if not _is_sequence_value(values[0]):
        return False
    if not _looks_like_account_value(values[1]):
        return False
    if not _looks_like_person_name(values[2]):
        return False
    return _looks_like_summary_text(values[3])


def _is_sequence_value(value: object) -> bool:
    if isinstance(value, int):
        return 0 < value < 100000
    text = str(value or "").strip()
    return text.isdigit() and 0 < int(text) < 100000


def _looks_like_account_value(value: object) -> bool:
    text = str(value or "").strip()
    return text.isdigit() and len(text) >= 6


def _looks_like_person_name(value: object) -> bool:
    text = str(value or "").strip()
    if not text or text.isdigit():
        return False
    return len(text) <= 20


def _looks_like_summary_text(value: object) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if text.isdigit():
        return False
    return any(token in text for token in ("登记", "汇缴", "补缴", "启封", "销户", "封存"))


def _clean_cell_value(value: object) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in PLACEHOLDER_STRINGS:
            return None
        return stripped
    return value


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    candidate = str(value).strip().replace(",", "")
    if not candidate or candidate.lower() in PLACEHOLDER_STRINGS:
        return None
    try:
        return Decimal(candidate)
    except InvalidOperation:
        return None


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    return value
