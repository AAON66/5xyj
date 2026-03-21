from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.mappings.manual_field_aliases import AliasRule, MANUAL_ALIAS_RULES
from backend.app.parsers import HeaderExtraction, HeaderColumn, extract_header_structure
from backend.app.services.llm_mapping_service import (
    LLMMappingResult,
    map_header_with_llm,
    map_header_with_llm_sync,
)


@dataclass(slots=True)
class HeaderMappingDecision:
    raw_header: str
    raw_header_signature: str
    canonical_field: str | None
    mapping_source: str
    confidence: float | None
    candidate_fields: list[str]
    matched_rules: list[str]
    llm_attempted: bool = False
    llm_status: str = "not_requested"
    rule_overrode_llm: bool = False


@dataclass(slots=True)
class HeaderNormalizationResult:
    source_file: str
    sheet_name: str
    raw_header_signature: str
    decisions: list[HeaderMappingDecision]
    unmapped_headers: list[str]


def normalize_headers(path: str | Path, region: str | None = None) -> HeaderNormalizationResult:
    extraction = extract_header_structure(path)
    return normalize_header_extraction(extraction, region=region)


def normalize_header_extraction(extraction: HeaderExtraction, region: str | None = None) -> HeaderNormalizationResult:
    decisions = [normalize_header_column(column, region=region) for column in extraction.columns]
    return HeaderNormalizationResult(
        source_file=extraction.source_file,
        sheet_name=extraction.sheet_name,
        raw_header_signature=extraction.raw_header_signature,
        decisions=decisions,
        unmapped_headers=[decision.raw_header_signature for decision in decisions if decision.canonical_field is None],
    )


async def normalize_header_extraction_with_fallback(
    extraction: HeaderExtraction,
    region: str | None = None,
    *,
    confidence_threshold: float = 0.8,
) -> HeaderNormalizationResult:
    decisions = []
    for column in extraction.columns:
        decision = normalize_header_column(column, region=region)
        if decision.canonical_field is not None:
            decisions.append(decision)
            continue
        decisions.append(
            await normalize_header_column_with_fallback(
                column,
                region=region,
                confidence_threshold=confidence_threshold,
            )
        )

    return HeaderNormalizationResult(
        source_file=extraction.source_file,
        sheet_name=extraction.sheet_name,
        raw_header_signature=extraction.raw_header_signature,
        decisions=decisions,
        unmapped_headers=[decision.raw_header_signature for decision in decisions if decision.canonical_field is None],
    )


def normalize_header_extraction_with_sync_fallback(
    extraction: HeaderExtraction,
    region: str | None = None,
    *,
    confidence_threshold: float = 0.8,
) -> HeaderNormalizationResult:
    decisions = []
    for column in extraction.columns:
        decision = normalize_header_column(column, region=region)
        if decision.canonical_field is not None:
            decisions.append(decision)
            continue
        decisions.append(
            normalize_header_column_with_sync_fallback(
                column,
                region=region,
                confidence_threshold=confidence_threshold,
            )
        )

    return HeaderNormalizationResult(
        source_file=extraction.source_file,
        sheet_name=extraction.sheet_name,
        raw_header_signature=extraction.raw_header_signature,
        decisions=decisions,
        unmapped_headers=[decision.raw_header_signature for decision in decisions if decision.canonical_field is None],
    )


async def normalize_headers_with_fallback(
    path: str | Path,
    region: str | None = None,
    *,
    confidence_threshold: float = 0.8,
) -> HeaderNormalizationResult:
    extraction = extract_header_structure(path)
    return await normalize_header_extraction_with_fallback(
        extraction,
        region=region,
        confidence_threshold=confidence_threshold,
    )


def normalize_headers_with_sync_fallback(
    path: str | Path,
    region: str | None = None,
    *,
    confidence_threshold: float = 0.8,
) -> HeaderNormalizationResult:
    extraction = extract_header_structure(path)
    return normalize_header_extraction_with_sync_fallback(
        extraction,
        region=region,
        confidence_threshold=confidence_threshold,
    )


def normalize_header_column(column: HeaderColumn, region: str | None = None) -> HeaderMappingDecision:
    matches: list[tuple[AliasRule, float]] = []
    for rule in MANUAL_ALIAS_RULES:
        if rule.matches(column.signature, region=region):
            match_score = rule.confidence + (0.005 if region and region in rule.regions else 0)
            matches.append((rule, match_score))

    matches.sort(key=lambda item: item[1], reverse=True)
    candidate_fields = _dedupe_preserve_order(rule.canonical_field for rule, _ in matches)
    matched_rules = [" + ".join(rule.patterns) for rule, _ in matches]

    top_match = matches[0] if matches else None
    return HeaderMappingDecision(
        raw_header=column.raw_header_parts[-1] if column.raw_header_parts else column.signature,
        raw_header_signature=column.signature,
        canonical_field=top_match[0].canonical_field if top_match else None,
        mapping_source="rule" if top_match else "unmapped",
        confidence=top_match[1] if top_match else None,
        candidate_fields=candidate_fields,
        matched_rules=matched_rules,
    )


async def normalize_header_column_with_fallback(
    column: HeaderColumn,
    region: str | None = None,
    *,
    confidence_threshold: float = 0.8,
) -> HeaderMappingDecision:
    decision = normalize_header_column(column, region=region)
    if decision.canonical_field is not None:
        return decision

    llm_result = await map_header_with_llm(column.signature, region=region)
    return _merge_llm_result(decision, llm_result, confidence_threshold=confidence_threshold)


def normalize_header_column_with_sync_fallback(
    column: HeaderColumn,
    region: str | None = None,
    *,
    confidence_threshold: float = 0.8,
) -> HeaderMappingDecision:
    decision = normalize_header_column(column, region=region)
    if decision.canonical_field is not None:
        return decision

    llm_result = map_header_with_llm_sync(column.signature, region=region)
    return _merge_llm_result(decision, llm_result, confidence_threshold=confidence_threshold)


def _merge_llm_result(
    decision: HeaderMappingDecision,
    llm_result: LLMMappingResult,
    *,
    confidence_threshold: float,
) -> HeaderMappingDecision:
    candidate_fields = _dedupe_preserve_order([*decision.candidate_fields, *llm_result.candidate_fields])
    llm_attempted = llm_result.status != "not_requested"

    if llm_result.canonical_field and (llm_result.confidence or 0) >= confidence_threshold:
        return HeaderMappingDecision(
            raw_header=decision.raw_header,
            raw_header_signature=decision.raw_header_signature,
            canonical_field=llm_result.canonical_field,
            mapping_source="llm",
            confidence=llm_result.confidence,
            candidate_fields=candidate_fields,
            matched_rules=decision.matched_rules,
            llm_attempted=llm_attempted,
            llm_status=llm_result.status,
            rule_overrode_llm=False,
        )

    return HeaderMappingDecision(
        raw_header=decision.raw_header,
        raw_header_signature=decision.raw_header_signature,
        canonical_field=None,
        mapping_source="unmapped",
        confidence=llm_result.confidence,
        candidate_fields=candidate_fields,
        matched_rules=decision.matched_rules,
        llm_attempted=llm_attempted,
        llm_status=llm_result.status,
        rule_overrode_llm=False,
    )


def _dedupe_preserve_order(values: object) -> list[str]:
    items = list(values)
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result
