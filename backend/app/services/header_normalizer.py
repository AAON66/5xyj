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


LLM_RELEVANCE_KEYWORDS = (
    '姓名', '名称', '证件', '身份证', '社保', '公积金', '养老', '医疗', '失业', '生育', '工伤', '补充', '大病', '滞纳金', '利息', '基数', '金额', '汇缴', '应缴', '合计', '总额', '编号', '账号', '账单', '年月', '所属月', '缴纳月', '缴费', '单位', '个人', '参保地'
)
LLM_IRRELEVANT_KEYWORDS = (
    '序号', '状态', '备注', '合作产品', '档案费', '制卡费', '工会费', '采暖费', '其它费用', '其他费用', '户籍性质', '起做时间', '服务费', '比例', '大病', '小计', '基数'
)

EXPLICIT_SKIP_SIGNATURE_KEYWORDS = (
    '费率',
    '社保缴纳档位',
    '调基补差预收',
    '残保金',
    '减免金额',
    '本金合计',
    '参保人员身份',
    '职业年金',
    '公务员医疗补助',
    '家属统筹医疗',
    '机关事业单位养老保险',
    '机关养老应缴费额',
    '公务员补助应缴费额',
    '离休人员医疗保障',
)
EXPLICIT_SKIP_SIGNATURE_KEYWORDS = EXPLICIT_SKIP_SIGNATURE_KEYWORDS + (
    '\u5e8f\u53f7',
    '\u5206\u7ec4',
    '\u4eba\u5458\u7f16\u53f7',
    '\u5f81\u6536\u9879\u76ee',
    '\u5f81\u6536\u54c1\u76ee',
    '\u5f81\u6536\u5b50\u76ee',
    '\u7533\u62a5\u65e5\u671f',
    '\u6570\u636e\u6765\u6e90',
    '\u7f34\u8d39\u7c7b\u578b',
    '\u4e3b\u7ba1\u7a0e\u52a1\u673a\u5173',
    '\u793e\u4fdd\u7ecf\u529e\u673a\u6784',
    '\u5355\u4f4d\u7f16\u53f7',
    '\u793e\u4fdd\u6d41\u6c34\u53f7',
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
    if not _should_attempt_llm_fallback(column.signature):
        return _build_skipped_irrelevant_decision(decision)

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
    if not _should_attempt_llm_fallback(column.signature):
        return _build_skipped_irrelevant_decision(decision)

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



def _should_attempt_llm_fallback(signature: str) -> bool:
    normalized_signature = signature.replace('\n', ' / ')
    if any(keyword in normalized_signature for keyword in EXPLICIT_SKIP_SIGNATURE_KEYWORDS):
        return False

    if any(keyword in normalized_signature for keyword in LLM_IRRELEVANT_KEYWORDS) and not any(
        keyword in normalized_signature for keyword in LLM_RELEVANCE_KEYWORDS
    ):
        return False

    if normalized_signature in ('社保', '公积金'):
        return False

    if any(
        keyword in normalized_signature
        for keyword in ('比例', '起做时间', '户籍性质', '大病', '小计', '差额', '住院', '门诊', '个账', '补充公积金', '补充公积')
    ):
        return False

    if '基数' in normalized_signature and not any(
        keyword in normalized_signature for keyword in ('缴费基数', '公积金企业基数', '公积金个人基数')
    ):
        return False

    if normalized_signature.endswith('合计') and any(
        keyword in normalized_signature for keyword in ('养老', '医疗', '失业', '工伤', '生育')
    ):
        return False

    return any(keyword in normalized_signature for keyword in LLM_RELEVANCE_KEYWORDS)


def _build_skipped_irrelevant_decision(decision: HeaderMappingDecision) -> HeaderMappingDecision:
    return HeaderMappingDecision(
        raw_header=decision.raw_header,
        raw_header_signature=decision.raw_header_signature,
        canonical_field=None,
        mapping_source='unmapped',
        confidence=None,
        candidate_fields=decision.candidate_fields,
        matched_rules=decision.matched_rules,
        llm_attempted=False,
        llm_status='skipped_irrelevant',
        rule_overrode_llm=False,
    )


def _dedupe_preserve_order(values: object) -> list[str]:
    items = list(values)
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result
