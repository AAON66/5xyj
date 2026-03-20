from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.mappings.manual_field_aliases import AliasRule, MANUAL_ALIAS_RULES, normalize_signature
from backend.app.parsers import HeaderExtraction, HeaderColumn, extract_header_structure


@dataclass(slots=True)
class HeaderMappingDecision:
    raw_header: str
    raw_header_signature: str
    canonical_field: str | None
    mapping_source: str
    confidence: float | None
    candidate_fields: list[str]
    matched_rules: list[str]


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


def _dedupe_preserve_order(values: list[str] | tuple[str, ...] | object) -> list[str]:
    items = list(values)
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result