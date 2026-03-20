from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.core.config import ROOT_DIR
from backend.app.parsers import extract_header_structure
from backend.app.services import normalize_header_column, normalize_header_extraction


SAMPLES_DIR = ROOT_DIR / "data" / "samples"


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob("*.xlsx")):
        if keyword in path.name:
            return path
    pytest.skip(f"Sample containing '{keyword}' was not found in {SAMPLES_DIR}.")


def decisions_by_signature(result) -> dict[str, object]:
    return {decision.raw_header_signature: decision for decision in result.decisions}


def test_normalize_header_column_leaves_rate_column_unmapped() -> None:
    extraction = extract_header_structure(find_sample("深圳创造欢乐"))
    rate_column = next(column for column in extraction.columns if column.signature == "基本养老保险（单位） / 费率")

    decision = normalize_header_column(rate_column, region="shenzhen")

    assert decision.canonical_field is None
    assert decision.mapping_source == "unmapped"
    assert decision.candidate_fields == []


def test_normalize_headers_on_real_guangzhou_sample() -> None:
    extraction = extract_header_structure(find_sample("广分"))
    result = normalize_header_extraction(extraction, region="guangzhou")
    decisions = decisions_by_signature(result)

    assert decisions["姓名"].canonical_field == "person_name"
    assert decisions["证件号码"].canonical_field == "id_number"
    assert decisions["证件类型"].canonical_field == "id_type"
    assert decisions["个人社保号"].canonical_field == "social_security_number"
    assert decisions["费款所属期起"].canonical_field == "period_start"
    assert decisions["费款所属期止"].canonical_field == "period_end"
    assert decisions["基本养老保险(单位缴纳) / 应缴金额"].canonical_field == "pension_company"
    assert decisions["基本养老保险(个人缴纳) / 应缴金额"].canonical_field == "pension_personal"
    assert decisions["失业保险(单位缴纳) / 应缴金额"].canonical_field == "unemployment_company"
    assert decisions["基本医疗保险（含生育）(单位缴纳) / 应缴金额"].canonical_field == "medical_maternity_company"


def test_normalize_headers_on_real_xiamen_sample() -> None:
    extraction = extract_header_structure(find_sample("厦门202602社保账单.xlsx"))
    result = normalize_header_extraction(extraction, region="xiamen")
    decisions = decisions_by_signature(result)

    assert decisions["总金额"].canonical_field == "total_amount"
    assert decisions["单位缴费总金额"].canonical_field == "company_total_amount"
    assert decisions["个人缴费总金额"].canonical_field == "personal_total_amount"
    assert decisions["建账年月"].canonical_field == "billing_period"
    assert decisions["费款所属期起"].canonical_field == "period_start"
    assert decisions["费款所属期止"].canonical_field == "period_end"
    assert decisions["城镇企业职工基本养老保险费 / 单位应缴"].canonical_field == "pension_company"
    assert decisions["城镇企业职工基本养老保险费 / 个人应缴"].canonical_field == "pension_personal"
    assert decisions["城镇企业职工基本养老保险费 / 滞纳金"].canonical_field == "late_fee"
    assert decisions["城镇企业职工基本养老保险费 / 利息"].canonical_field == "interest"


def test_normalize_headers_on_real_shenzhen_sample() -> None:
    extraction = extract_header_structure(find_sample("深圳创造欢乐"))
    result = normalize_header_extraction(extraction, region="shenzhen")
    decisions = decisions_by_signature(result)

    assert decisions["应收金额"].canonical_field == "total_amount"
    assert decisions["个人社保合计"].canonical_field == "personal_total_amount"
    assert decisions["单位社保合计"].canonical_field == "company_total_amount"
    assert decisions["缴费工资"].canonical_field == "payment_salary"
    assert decisions["基本养老保险（单位） / 应缴费额"].canonical_field == "pension_company"
    assert decisions["基本养老保险（个人） / 应缴费额"].canonical_field == "pension_personal"
    assert decisions["基本医疗保险（单位） / 应缴费额"].canonical_field == "medical_company"
    assert decisions["地方补充医疗（单位） / 应缴费额"].canonical_field == "supplementary_medical_company"


def test_normalize_headers_on_real_wuhan_sample() -> None:
    extraction = extract_header_structure(find_sample("武汉"))
    result = normalize_header_extraction(extraction, region="wuhan")
    decisions = decisions_by_signature(result)

    assert decisions["职工明细 / 姓名"].canonical_field == "person_name"
    assert decisions["职工明细 / 证件类型"].canonical_field == "id_type"
    assert decisions["职工明细 / 证件号码"].canonical_field == "id_number"
    assert decisions["职工明细 / 缴费工资"].canonical_field == "payment_salary"
    assert decisions["职工明细 / 缴费基数"].canonical_field == "payment_base"
    assert decisions["单位缴纳 / 养老保险应缴费额"].canonical_field == "pension_company"
    assert decisions["个人缴纳 / 养老保险应缴费额"].canonical_field == "pension_personal"
    assert decisions["单位缴纳 / 工伤保险应缴费额"].canonical_field == "injury_company"


def test_normalize_headers_on_real_changsha_sample() -> None:
    extraction = extract_header_structure(find_sample("长沙"))
    result = normalize_header_extraction(extraction, region="changsha")
    decisions = decisions_by_signature(result)

    assert decisions["求和项:应缴费额 / 姓名"].canonical_field == "person_name"
    assert decisions["征收品目 / 工伤保险"].canonical_field == "injury_company"
    assert decisions["失业保险(单位缴纳)"].canonical_field == "unemployment_company"
    assert decisions["失业保险(个人缴纳)"].canonical_field == "unemployment_personal"
    assert decisions["职工大额医疗互助保险(个人缴纳)"].canonical_field == "large_medical_personal"
    assert decisions["总计"].canonical_field == "total_amount"