from __future__ import annotations

from datetime import date, datetime
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional

from backend.app.models.enums import SourceFileKind
from backend.app.models.normalized_record import NormalizedRecord
from backend.app.parsers import HeaderExtraction, extract_header_structure
from backend.app.parsers.workbook_loader import load_workbook_compatible
from backend.app.services.header_normalizer import (
    HeaderMappingDecision,
    HeaderNormalizationResult,
    normalize_header_extraction,
    normalize_header_extraction_with_fallback,
)
from backend.app.utils.period_utils import (
    coalesce_billing_period,
    infer_billing_period_from_filename,
    normalize_billing_period,
    normalize_period_boundary,
)
from backend.app.validators import RowFilterDecision, classify_row

AMOUNT_FIELDS = {
    "payment_base",
    "payment_salary",
    "housing_fund_base",
    "housing_fund_personal",
    "housing_fund_company",
    "housing_fund_total",
    "total_amount",
    "company_total_amount",
    "personal_total_amount",
    "pension_company",
    "pension_personal",
    "medical_company",
    "medical_personal",
    "medical_maternity_company",
    "maternity_amount",
    "unemployment_company",
    "unemployment_personal",
    "injury_company",
    "supplementary_medical_company",
    "supplementary_pension_company",
    "large_medical_personal",
    "late_fee",
    "interest",
}

PLACEHOLDER_STRINGS = {"", "-", "--", "??", "none", "null", "(??)"}
CHANGSHA_TRANSACTION_ITEM_FIELD_MAP = {
    "职工基本养老保险(单位缴纳)": "pension_company",
    "职工基本养老保险(个人缴纳)": "pension_personal",
    "职工基本医疗保险(单位缴纳)": "medical_company",
    "职工基本医疗保险(个人缴纳)": "medical_personal",
    "失业保险(单位缴纳)": "unemployment_company",
    "失业保险(个人缴纳)": "unemployment_personal",
    "工伤保险": "injury_company",
    "生育保险(单位缴纳)": "maternity_amount",
    "职工大额医疗互助保险(个人缴纳)": "large_medical_personal",
}
WUHAN_TRANSACTION_FILL_DOWN_HEADERS = {
    "\u59d3\u540d",
    "\u8bc1\u4ef6\u53f7\u7801",
    "\u8d39\u6b3e\u6240\u5c5e\u671f",
    "\u6570\u636e\u6765\u6e90",
    "\u7f34\u8d39\u7c7b\u578b",
    "\u4e3b\u7ba1\u7a0e\u52a1\u673a\u5173",
    "\u793e\u4fdd\u7ecf\u529e\u673a\u6784",
}
WUHAN_TRANSACTION_COMMON_FIELDS = (
    "person_name",
    "id_type",
    "id_number",
    "employee_id",
    "social_security_number",
    "company_name",
    "region",
    "billing_period",
    "period_start",
    "period_end",
    "payment_base",
    "payment_salary",
    "raw_sheet_name",
    "raw_header_signature",
    "source_file_name",
)
WUHAN_TRANSACTION_ITEM_FIELD_MAP = {
    "\u4f01\u4e1a\u804c\u5de5\u57fa\u672c\u517b\u8001\u4fdd\u9669": ("pension_company", "pension_personal"),
    "\u5931\u4e1a\u4fdd\u9669": ("unemployment_company", "unemployment_personal"),
    "\u5de5\u4f24\u4fdd\u9669": ("injury_company", None),
    "\u4f01\u4e1a\u804c\u5de5\u57fa\u672c\u533b\u7597\u4fdd\u9669": ("medical_company", "medical_personal"),
    "\u804c\u5de5\u5927\u989d\u533b\u7597\u4e92\u52a9\u4fdd\u9669": (None, "large_medical_personal"),
}
MERGE_VALUE_FIELDS = (
    "person_name",
    "id_type",
    "id_number",
    "employee_id",
    "social_security_number",
    "company_name",
    "region",
    "billing_period",
    "period_start",
    "period_end",
    "payment_base",
    "payment_salary",
    "housing_fund_account",
    "housing_fund_base",
    "housing_fund_personal",
    "housing_fund_company",
    "housing_fund_total",
    "total_amount",
    "company_total_amount",
    "personal_total_amount",
    "pension_company",
    "pension_personal",
    "medical_company",
    "medical_personal",
    "medical_maternity_company",
    "maternity_amount",
    "unemployment_company",
    "unemployment_personal",
    "injury_company",
    "supplementary_medical_company",
    "supplementary_pension_company",
    "large_medical_personal",
    "late_fee",
    "interest",
    "raw_sheet_name",
    "raw_header_signature",
    "source_file_name",
)


@dataclass
class NormalizedPreviewRecord:
    source_row_number: int
    values: dict[str, Any]
    unmapped_values: dict[str, Any]
    raw_values: dict[str, Any]
    raw_payload: dict[str, Any]


@dataclass
class StandardizationResult:
    source_file: str
    sheet_name: str
    raw_header_signature: str
    records: list[NormalizedPreviewRecord]
    filtered_rows: list[RowFilterDecision]
    unmapped_headers: list[str]


@dataclass
class SourceRecordBundle:
    source_file_id: str
    source_file_name: str
    source_kind: str
    standardized: StandardizationResult


@dataclass
class _MergedRecordEntry:
    source_file_id: str
    source_row_number: int
    values: dict[str, Any]
    raw_payload: dict[str, Any]


def standardize_workbook(
    path: str | Path,
    *,
    region: Optional[str] = None,
    company_name: Optional[str] = None,
    source_file_name: Optional[str] = None,
    extraction: Optional[HeaderExtraction] = None,
    normalization: Optional[HeaderNormalizationResult] = None,
) -> StandardizationResult:
    workbook_path = Path(path)
    runtime_extraction = extraction or extract_header_structure(workbook_path)
    runtime_normalization = normalization or normalize_header_extraction(runtime_extraction, region=region)
    return _standardize_rows(
        workbook_path,
        runtime_extraction,
        runtime_normalization,
        region=region,
        company_name=company_name,
        source_file_name=source_file_name,
    )


async def standardize_workbook_with_fallback(
    path: str | Path,
    *,
    region: Optional[str] = None,
    company_name: Optional[str] = None,
    source_file_name: Optional[str] = None,
    confidence_threshold: float = 0.8,
    extraction: Optional[HeaderExtraction] = None,
    normalization: Optional[HeaderNormalizationResult] = None,
) -> StandardizationResult:
    workbook_path = Path(path)
    runtime_extraction = extraction or extract_header_structure(workbook_path)
    runtime_normalization = normalization or await normalize_header_extraction_with_fallback(
        runtime_extraction,
        region=region,
        confidence_threshold=confidence_threshold,
    )
    return _standardize_rows(
        workbook_path,
        runtime_extraction,
        runtime_normalization,
        region=region,
        company_name=company_name,
        source_file_name=source_file_name,
    )


def build_normalized_models(
    result: StandardizationResult,
    *,
    batch_id: str,
    source_file_id: str,
) -> list[NormalizedRecord]:
    records: list[NormalizedRecord] = []
    for preview in result.records:
        model_kwargs = {
            "batch_id": batch_id,
            "source_file_id": source_file_id,
            "source_row_number": preview.source_row_number,
            "raw_sheet_name": result.sheet_name,
            "raw_header_signature": result.raw_header_signature,
            "source_file_name": result.source_file,
            "raw_payload": preview.raw_payload,
        }
        model_kwargs.update(preview.values)
        records.append(NormalizedRecord(**model_kwargs))
    return records


def merge_batch_standardized_records(
    source_bundles: list[SourceRecordBundle],
    *,
    batch_id: str,
) -> list[NormalizedRecord]:
    social_bundles = [item for item in source_bundles if item.source_kind == SourceFileKind.SOCIAL_SECURITY.value]
    housing_bundles = [item for item in source_bundles if item.source_kind == SourceFileKind.HOUSING_FUND.value]

    entries: list[_MergedRecordEntry] = []
    index: dict[tuple[str, ...], list[_MergedRecordEntry]] = {}

    base_bundles = social_bundles if social_bundles else housing_bundles
    for bundle in base_bundles:
        for record in bundle.standardized.records:
            entry = _create_entry(bundle, record)
            entries.append(entry)
            key = _merge_key(record)
            if key is not None:
                index.setdefault(key, []).append(entry)

    if social_bundles:
        overlay_bundles = housing_bundles
    else:
        overlay_bundles = []

    for bundle in overlay_bundles:
        for record in bundle.standardized.records:
            key = _merge_key(record)
            matches = index.get(key, []) if key is not None else []
            if len(matches) != 1:
                fallback_matches = _find_fallback_merge_matches(record, entries)
                if len(fallback_matches) == 1:
                    matches = fallback_matches
            if len(matches) == 1:
                _merge_entry(matches[0], bundle, record)
                continue
            entry = _create_entry(bundle, record)
            entries.append(entry)
            if key is not None:
                index.setdefault(key, []).append(entry)

    models: list[NormalizedRecord] = []
    for entry in entries:
        model_kwargs = {
            "batch_id": batch_id,
            "source_file_id": entry.source_file_id,
            "source_row_number": entry.source_row_number,
            "raw_payload": entry.raw_payload,
        }
        for field_name in MERGE_VALUE_FIELDS:
            value = entry.values.get(field_name)
            if value is not None:
                model_kwargs[field_name] = value
        models.append(NormalizedRecord(**model_kwargs))
    return models


def _create_entry(bundle: SourceRecordBundle, record: NormalizedPreviewRecord) -> _MergedRecordEntry:
    raw_payload = {
        **record.raw_payload,
        "merged_sources": [
            {
                "source_kind": bundle.source_kind,
                "source_file_id": bundle.source_file_id,
                "source_file_name": bundle.source_file_name,
                "sheet_name": bundle.standardized.sheet_name,
                "raw_header_signature": bundle.standardized.raw_header_signature,
                "source_row_number": record.source_row_number,
                "raw_values": {_key: _json_safe(_value) for _key, _value in record.raw_values.items()},
                "unmapped_values": {_key: _json_safe(_value) for _key, _value in record.unmapped_values.items()},
            }
        ],
    }
    return _MergedRecordEntry(
        source_file_id=bundle.source_file_id,
        source_row_number=record.source_row_number,
        values=dict(record.values),
        raw_payload=raw_payload,
    )


def _merge_entry(entry: _MergedRecordEntry, bundle: SourceRecordBundle, record: NormalizedPreviewRecord) -> None:
    for field_name, value in record.values.items():
        existing = entry.values.get(field_name)
        if existing is None and value is not None:
            entry.values[field_name] = value
            continue
        if value is None or existing == value:
            continue
        conflicts = entry.raw_payload.setdefault("merged_field_conflicts", {})
        values = conflicts.setdefault(field_name, [])
        for item in (existing, value):
            safe_item = _json_safe(item)
            if safe_item not in values:
                values.append(safe_item)

    merged_sources = entry.raw_payload.setdefault("merged_sources", [])
    merged_sources.append(
        {
            "source_kind": bundle.source_kind,
            "source_file_id": bundle.source_file_id,
            "source_file_name": bundle.source_file_name,
            "sheet_name": bundle.standardized.sheet_name,
            "raw_header_signature": bundle.standardized.raw_header_signature,
            "source_row_number": record.source_row_number,
            "raw_values": {key: _json_safe(value) for key, value in record.raw_values.items()},
            "unmapped_values": {key: _json_safe(value) for key, value in record.unmapped_values.items()},
        }
    )


def _merge_key(record: NormalizedPreviewRecord) -> tuple[str, ...] | None:
    id_number = _normalize_identity_value(record.values.get("id_number"))
    company_name = _normalize_identity_value(record.values.get("company_name"))
    person_name = _normalize_identity_value(record.values.get("person_name"))

    if id_number and company_name:
        return ("id_company", id_number, company_name)
    if id_number:
        return ("id", id_number)
    if person_name and company_name:
        return ("name_company", person_name, company_name)
    if person_name:
        return ("name", person_name)
    return None


def _find_fallback_merge_matches(
    record: NormalizedPreviewRecord,
    entries: list[_MergedRecordEntry],
) -> list[_MergedRecordEntry]:
    record_id_number = _normalize_identity_value(record.values.get("id_number"))
    if record_id_number is not None:
        id_matches = [
            entry for entry in entries if _normalize_identity_value(entry.values.get("id_number")) == record_id_number
        ]
        if len(id_matches) == 1:
            return id_matches

    record_name = _normalize_identity_value(record.values.get("person_name"))
    if record_name is None:
        return []

    record_region = _normalize_identity_value(record.values.get("region"))
    record_company = _normalize_identity_value(record.values.get("company_name"))

    name_matches = [
        entry for entry in entries if _normalize_identity_value(entry.values.get("person_name")) == record_name
    ]
    if len(name_matches) <= 1:
        return name_matches

    company_and_region_matches = [
        entry
        for entry in name_matches
        if _values_match(record_region, _normalize_identity_value(entry.values.get("region")))
        and _values_match(record_company, _normalize_identity_value(entry.values.get("company_name")))
    ]
    if len(company_and_region_matches) == 1:
        return company_and_region_matches

    region_only_matches = [
        entry
        for entry in name_matches
        if _values_match(record_region, _normalize_identity_value(entry.values.get("region")))
    ]
    if len(region_only_matches) == 1:
        return region_only_matches

    company_only_matches = [
        entry
        for entry in name_matches
        if _values_match(record_company, _normalize_identity_value(entry.values.get("company_name")))
    ]
    if len(company_only_matches) == 1:
        return company_only_matches

    return []


def _values_match(left: Optional[str], right: Optional[str]) -> bool:
    if left is None or right is None:
        return False
    return left == right


def _normalize_identity_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip().lower()
    return text or None


def _standardize_rows(
    workbook_path: Path,
    extraction: HeaderExtraction,
    normalization: HeaderNormalizationResult,
    *,
    region: Optional[str],
    company_name: Optional[str],
    source_file_name: Optional[str],
) -> StandardizationResult:
    workbook = load_workbook_compatible(workbook_path, read_only=True, data_only=True)
    try:
        sheet = workbook[extraction.sheet_name]
        max_column = max(column.column_index for column in extraction.columns)
        rows = list(
            sheet.iter_rows(
                min_row=extraction.data_start_row,
                max_row=sheet.max_row,
                max_col=max_column,
                values_only=True,
            )
        )
    finally:
        workbook.close()

    records: list[NormalizedPreviewRecord] = []
    filtered_rows: list[RowFilterDecision] = []
    wuhan_transactional = _is_wuhan_transactional_extraction(extraction, region=region)
    carry_forward_values: dict[str, Any] = {}
    row_number = extraction.data_start_row
    for row in rows:
        selected_values = [row[column.column_index - 1] for column in extraction.columns]
        filter_decision = classify_row(selected_values, row_number=row_number)
        if not filter_decision.keep:
            filtered_rows.append(filter_decision)
            row_number += 1
            continue

        if wuhan_transactional:
            selected_values = _fill_down_wuhan_transactional_values(
                selected_values,
                columns=extraction.columns,
                carry_forward_values=carry_forward_values,
            )

        records.append(
            _build_preview_record(
                selected_values,
                extraction=extraction,
                decisions=normalization.decisions,
                region=region,
                company_name=company_name,
                source_file_name=source_file_name or workbook_path.name,
                row_number=row_number,
            )
        )
        row_number += 1

    if wuhan_transactional:
        records = _collapse_wuhan_transactional_records(records)

    return StandardizationResult(
        source_file=source_file_name or workbook_path.name,
        sheet_name=extraction.sheet_name,
        raw_header_signature=extraction.raw_header_signature,
        records=records,
        filtered_rows=filtered_rows,
        unmapped_headers=normalization.unmapped_headers,
    )


def _build_preview_record(
    selected_values: list[object],
    *,
    extraction: HeaderExtraction,
    decisions: list[HeaderMappingDecision],
    region: Optional[str],
    company_name: Optional[str],
    source_file_name: str,
    row_number: int,
) -> NormalizedPreviewRecord:
    raw_values: dict[str, Any] = {}
    values: dict[str, Any] = {
        "company_name": company_name,
        "region": region,
        "raw_sheet_name": extraction.sheet_name,
        "raw_header_signature": extraction.raw_header_signature,
        "source_file_name": source_file_name,
    }
    unmapped_values: dict[str, Any] = {}
    field_conflicts: dict[str, list[Any]] = {}

    for column, decision, raw_value in zip(extraction.columns, decisions, selected_values, strict=True):
        cleaned_raw = _clean_cell_value(raw_value)
        raw_values[column.signature] = cleaned_raw
        if decision.canonical_field is None:
            if cleaned_raw is not None:
                unmapped_values[column.signature] = cleaned_raw
            continue

        canonical_value = _coerce_canonical_value(decision.canonical_field, cleaned_raw)
        if canonical_value is None:
            continue
        _assign_canonical_value(values, field_conflicts, decision.canonical_field, canonical_value)

    _apply_region_specific_row_mappings(
        values,
        raw_values,
        field_conflicts,
        region=region,
    )
    _derive_period_fields(values, source_file_name=source_file_name, raw_header_signature=extraction.raw_header_signature)
    raw_payload = {
        "raw_values": {key: _json_safe(value) for key, value in raw_values.items()},
        "unmapped_values": {key: _json_safe(value) for key, value in unmapped_values.items()},
    }
    if field_conflicts:
        raw_payload["field_conflicts"] = {
            key: [_json_safe(value) for value in conflict_values]
            for key, conflict_values in field_conflicts.items()
        }

    return NormalizedPreviewRecord(
        source_row_number=row_number,
        values=values,
        unmapped_values=unmapped_values,
        raw_values=raw_values,
        raw_payload=raw_payload,
    )


def _assign_canonical_value(
    values: dict[str, Any],
    field_conflicts: dict[str, list[Any]],
    field_name: str,
    value: Any,
) -> None:
    existing = values.get(field_name)
    if existing is None:
        values[field_name] = value
        return
    if existing == value:
        return
    field_conflicts.setdefault(field_name, [existing]).append(value)


def _apply_region_specific_row_mappings(
    values: dict[str, Any],
    raw_values: dict[str, Any],
    field_conflicts: dict[str, list[Any]],
    *,
    region: Optional[str],
) -> None:
    if region == "changsha":
        _apply_changsha_transaction_item_mapping(values, raw_values, field_conflicts)


def _is_wuhan_transactional_extraction(extraction: HeaderExtraction, *, region: Optional[str]) -> bool:
    if region != "wuhan":
        return False

    normalized_signatures = {
        _normalize_business_text(column.signature)
        for column in extraction.columns
    }
    return (
        "\u9669\u79cd" in normalized_signatures
        and "\u5355\u4f4d\u90e8\u5206/\u5e94\u7f34\u8d39\u989d(\u5143)" in normalized_signatures
        and "\u4e2a\u4eba\u90e8\u5206/\u5e94\u7f34\u8d39\u989d(\u5143)" in normalized_signatures
    )


def _fill_down_wuhan_transactional_values(
    selected_values: list[object],
    *,
    columns: list[Any],
    carry_forward_values: dict[str, Any],
) -> list[object]:
    filled_values = list(selected_values)
    for index, (column, raw_value) in enumerate(zip(columns, selected_values, strict=True)):
        normalized_signature = _normalize_business_text(column.signature)
        if normalized_signature not in WUHAN_TRANSACTION_FILL_DOWN_HEADERS:
            continue

        cleaned_value = _clean_cell_value(raw_value)
        if cleaned_value is None:
            fallback_value = carry_forward_values.get(normalized_signature)
            if fallback_value is not None:
                filled_values[index] = fallback_value
            continue

        carry_forward_values[normalized_signature] = cleaned_value
    return filled_values


def _collapse_wuhan_transactional_records(records: list[NormalizedPreviewRecord]) -> list[NormalizedPreviewRecord]:
    merged_records: dict[tuple[str, ...], dict[str, Any]] = {}
    ordered_keys: list[tuple[str, ...]] = []

    for record in records:
        key = _build_wuhan_transactional_merge_key(record)
        if key is None:
            key = ("row", str(record.source_row_number))
        if key not in merged_records:
            ordered_keys.append(key)
            merged_records[key] = {
                "source_row_number": record.source_row_number,
                "values": {},
                "raw_values": dict(record.raw_values),
                "unmapped_values": dict(record.unmapped_values),
                "raw_payload": {
                    "merge_strategy": "wuhan_transactional_by_insurance_item",
                    "merged_sources": [],
                },
            }

        aggregate = merged_records[key]
        _merge_wuhan_common_values(aggregate["values"], record.values)
        _merge_wuhan_unmapped_values(aggregate["unmapped_values"], record.unmapped_values)
        _append_wuhan_merged_source(aggregate["raw_payload"], record)
        _accumulate_wuhan_transactional_amounts(aggregate["values"], record)

    return [
        NormalizedPreviewRecord(
            source_row_number=merged_records[key]["source_row_number"],
            values=merged_records[key]["values"],
            unmapped_values=merged_records[key]["unmapped_values"],
            raw_values=merged_records[key]["raw_values"],
            raw_payload=merged_records[key]["raw_payload"],
        )
        for key in ordered_keys
    ]


def _build_wuhan_transactional_merge_key(record: NormalizedPreviewRecord) -> tuple[str, ...] | None:
    id_number = _normalize_identity_value(record.values.get("id_number"))
    person_name = _normalize_identity_value(record.values.get("person_name"))
    billing_period = _normalize_identity_value(record.values.get("billing_period"))

    if id_number and billing_period:
        return ("id_period", id_number, billing_period)
    if person_name and billing_period:
        return ("name_period", person_name, billing_period)
    if id_number:
        return ("id", id_number)
    if person_name:
        return ("name", person_name)
    return None


def _merge_wuhan_common_values(target: dict[str, Any], source: dict[str, Any]) -> None:
    for field_name in WUHAN_TRANSACTION_COMMON_FIELDS:
        value = source.get(field_name)
        if value is None:
            continue

        if field_name in {"payment_base", "payment_salary"}:
            existing = _to_decimal(target.get(field_name))
            candidate = _to_decimal(value)
            if candidate is None:
                continue
            if existing is None or candidate > existing:
                target[field_name] = candidate
            continue

        if target.get(field_name) is None:
            target[field_name] = value


def _merge_wuhan_unmapped_values(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if key not in target and value is not None:
            target[key] = value


def _append_wuhan_merged_source(raw_payload: dict[str, Any], record: NormalizedPreviewRecord) -> None:
    merged_sources = raw_payload.setdefault("merged_sources", [])
    merged_sources.append(
        {
            "source_row_number": record.source_row_number,
            "raw_values": {key: _json_safe(value) for key, value in record.raw_values.items()},
            "unmapped_values": {key: _json_safe(value) for key, value in record.unmapped_values.items()},
        }
    )


def _accumulate_wuhan_transactional_amounts(target: dict[str, Any], record: NormalizedPreviewRecord) -> None:
    total_amount = _to_decimal(record.values.get("total_amount"))
    company_amount = _to_decimal(
        _find_raw_value_by_header(record.raw_values, "\u5355\u4f4d\u90e8\u5206 / \u5e94\u7f34\u8d39\u989d(\u5143)")
    )
    personal_amount = _to_decimal(
        _find_raw_value_by_header(record.raw_values, "\u4e2a\u4eba\u90e8\u5206 / \u5e94\u7f34\u8d39\u989d(\u5143)")
    )

    _sum_decimal_field(target, "total_amount", total_amount)
    _sum_decimal_field(target, "company_total_amount", company_amount)
    _sum_decimal_field(target, "personal_total_amount", personal_amount)

    item_name = _normalize_business_text(_find_raw_value_by_header(record.raw_values, "\u9669\u79cd"))
    field_mapping = WUHAN_TRANSACTION_ITEM_FIELD_MAP.get(item_name)
    if field_mapping is None:
        return

    company_field, personal_field = field_mapping
    if company_field is not None and company_amount is not None:
        target[company_field] = company_amount
    if personal_field is not None and personal_amount is not None:
        target[personal_field] = personal_amount


def _sum_decimal_field(values: dict[str, Any], field_name: str, amount: Optional[Decimal]) -> None:
    if amount is None:
        return

    existing = _to_decimal(values.get(field_name))
    values[field_name] = (existing or Decimal("0")) + amount


def _apply_changsha_transaction_item_mapping(
    values: dict[str, Any],
    raw_values: dict[str, Any],
    field_conflicts: dict[str, list[Any]],
) -> None:
    item_name = _normalize_business_text(_find_raw_value_by_header(raw_values, "征收品目"))
    if item_name is None:
        return

    field_name = CHANGSHA_TRANSACTION_ITEM_FIELD_MAP.get(item_name)
    if field_name is None:
        return

    amount = _to_decimal(values.get("total_amount"))
    if amount is None:
        amount = _to_decimal(_find_raw_value_by_header(raw_values, "应缴费额"))
    if amount is None:
        return

    _assign_canonical_value(values, field_conflicts, field_name, amount)


def _derive_period_fields(
    values: dict[str, Any],
    *,
    source_file_name: Optional[str] = None,
    raw_header_signature: Optional[str] = None,
) -> None:
    period_start = normalize_period_boundary(values.get("period_start")) or values.get("period_start")
    period_end = normalize_period_boundary(values.get("period_end")) or values.get("period_end")
    billing_period = coalesce_billing_period(
        values.get("billing_period"),
        period_start,
        period_end,
        raw_header_signature,
        infer_billing_period_from_filename(source_file_name),
    )

    if billing_period:
        values["billing_period"] = billing_period

    if period_start is not None:
        values["period_start"] = period_start
    if period_end is not None:
        values["period_end"] = period_end

    if not values.get("period_start") and billing_period:
        values["period_start"] = billing_period
    if not values.get("period_end") and billing_period:
        values["period_end"] = billing_period


def _find_raw_value_by_header(raw_values: dict[str, Any], header_name: str) -> Any:
    target = _normalize_business_text(header_name)
    for raw_key, raw_value in raw_values.items():
        if _normalize_business_text(raw_key) == target:
            return raw_value
    return None


def _coerce_canonical_value(field_name: str, value: Any) -> Any:
    if value is None:
        return None
    if field_name in AMOUNT_FIELDS:
        return _to_decimal(value)
    if isinstance(value, datetime):
        if field_name == "billing_period":
            return value.strftime("%Y-%m")
        return value.date().isoformat()
    if isinstance(value, date):
        if field_name == "billing_period":
            return value.strftime("%Y-%m")
        return value.isoformat()
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if field_name == "billing_period":
            return normalize_billing_period(stripped)
        if field_name in {"period_start", "period_end"}:
            return normalize_period_boundary(stripped) or stripped
        return stripped
    return value


def _clean_cell_value(value: object) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in PLACEHOLDER_STRINGS:
            return None
        return stripped
    return value


def _normalize_business_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.replace(" ", "").replace("（", "(").replace("）", ")")


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        candidate = value.strip().replace(",", "")
        if not candidate or candidate.lower() in PLACEHOLDER_STRINGS:
            return None
        try:
            return Decimal(candidate)
        except InvalidOperation:
            return None
    return None


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value
