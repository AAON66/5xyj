from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from backend.app.core.config import ROOT_DIR
from backend.app.parsers import discover_workbook, extract_header_structure
from backend.app.services import standardize_workbook

SAMPLES_DIR = ROOT_DIR / "data" / "samples"


@dataclass(frozen=True, slots=True)
class RegionRegressionCase:
    keyword: str
    region: str
    expected_sheet: str
    expected_header_rows: list[int]
    expected_data_start_row: int
    min_records: int
    required_fields: tuple[str, ...]
    expected_filtered_reasons: tuple[str, ...] = ()


REGION_REGRESSION_CASES = [
    RegionRegressionCase(
        keyword="\u5e7f\u5206",
        region="guangzhou",
        expected_sheet="sheet1",
        expected_header_rows=[7, 8],
        expected_data_start_row=9,
        min_records=2,
        required_fields=(
            "person_name",
            "id_number",
            "social_security_number",
            "billing_period",
            "company_total_amount",
            "personal_total_amount",
            "pension_company",
        ),
    ),
    RegionRegressionCase(
        keyword="\u676d\u5dde\u805a\u53d8",
        region="hangzhou",
        expected_sheet="Sheet1",
        expected_header_rows=[3, 4],
        expected_data_start_row=5,
        min_records=1,
        required_fields=(
            "person_name",
            "id_number",
            "pension_company",
            "pension_personal",
            "medical_company",
            "medical_personal",
        ),
        expected_filtered_reasons=("summary_total",),
    ),
    RegionRegressionCase(
        keyword="\u53a6\u95e8202602\u793e\u4fdd\u8d26\u5355.xlsx",
        region="xiamen",
        expected_sheet="\u804c\u5de5\u793e\u4fdd\u5bf9\u8d26\u5355\u660e\u7ec6\u67e5\u8be2",
        expected_header_rows=[3, 4],
        expected_data_start_row=5,
        min_records=1,
        required_fields=(
            "person_name",
            "id_number",
            "billing_period",
            "period_start",
            "period_end",
            "total_amount",
            "company_total_amount",
            "personal_total_amount",
        ),
        expected_filtered_reasons=("summary_total",),
    ),
    RegionRegressionCase(
        keyword="\u6df1\u5733\u521b\u9020\u6b22\u4e50",
        region="shenzhen",
        expected_sheet="\u7533\u62a5\u660e\u7ec6",
        expected_header_rows=[1, 2],
        expected_data_start_row=4,
        min_records=2,
        required_fields=(
            "person_name",
            "id_number",
            "total_amount",
            "company_total_amount",
            "personal_total_amount",
            "supplementary_pension_company",
        ),
        expected_filtered_reasons=("summary_subtotal", "group_header"),
    ),
    RegionRegressionCase(
        keyword="\u6b66\u6c49",
        region="wuhan",
        expected_sheet="Sheet1",
        expected_header_rows=[1, 2],
        expected_data_start_row=3,
        min_records=1,
        required_fields=(
            "person_name",
            "payment_base",
            "payment_salary",
            "pension_company",
            "pension_personal",
            "medical_company",
            "medical_personal",
        ),
        expected_filtered_reasons=("summary_total",),
    ),
    RegionRegressionCase(
        keyword="\u957f\u6c99",
        region="changsha",
        expected_sheet="Sheet4",
        expected_header_rows=[3, 4],
        expected_data_start_row=5,
        min_records=1,
        required_fields=(
            "person_name",
            "pension_company",
            "medical_company",
            "unemployment_personal",
            "large_medical_personal",
            "total_amount",
        ),
    ),
]


KNOWN_SAMPLE_CASES: tuple[tuple[str, str], ...] = (
    ("\u5e7f\u5206", "guangzhou"),
    ("\u89c6\u64ad", "guangzhou"),
    ("\u676d\u5dde\u805a\u53d8", "hangzhou"),
    ("\u676d\u5dde\u88c2\u53d8", "hangzhou"),
    ("\u53a6\u95e8202602\u793e\u4fdd\u8d26\u5355.xlsx", "xiamen"),
    ("\u53a6\u95e8202602\u793e\u4fdd\u8d26\u5355\uff08\u8865\u7f341\u6708\u5165\u804c2\u4eba\uff09", "xiamen"),
    ("\u6df1\u5733\u521b\u9020\u6b22\u4e50", "shenzhen"),
    ("\u6df1\u5733\u96f6\u4e00\u91d1\u667a", "shenzhen"),
    ("\u6df1\u5733\u96f6\u4e00\u88c2\u53d8", "shenzhen"),
    ("\u6df1\u5733\u96f6\u4e00\u6570\u79d1", "shenzhen"),
    ("\u6df1\u5733\u96f6\u4e00\u8fd0\u8425", "shenzhen"),
    ("\u6df1\u5733\u9752\u6625\u6d0b\u6ea2", "shenzhen"),
    ("\u6df1\u5733\u65e0\u9650\u589e\u957f", "shenzhen"),
    ("\u5218\u8273\u73b2", "shenzhen"),
    ("\u6b66\u6c49", "wuhan"),
    ("\u957f\u6c99", "changsha"),
)


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob("*.xlsx")):
        if keyword in path.name:
            return path
    pytest.skip(f"Sample containing {keyword!r} was not found in {SAMPLES_DIR}.")


@pytest.mark.parametrize(
    "case",
    REGION_REGRESSION_CASES,
    ids=[case.region for case in REGION_REGRESSION_CASES],
)
def test_region_sample_pipeline_regression(case: RegionRegressionCase) -> None:
    sample_path = find_sample(case.keyword)

    discovery = discover_workbook(sample_path)
    extraction = extract_header_structure(sample_path)
    result = standardize_workbook(sample_path, region=case.region)

    assert discovery.selected_sheet_name == case.expected_sheet
    assert extraction.sheet_name == case.expected_sheet
    assert extraction.header_rows == case.expected_header_rows
    assert extraction.data_start_row == case.expected_data_start_row
    assert result.sheet_name == case.expected_sheet
    assert len(result.records) >= case.min_records

    first = result.records[0]
    for field_name in case.required_fields:
        assert first.values[field_name] is not None, f"Expected {field_name} for {sample_path.name}"

    filtered_reasons = {row.reason for row in result.filtered_rows}
    for reason in case.expected_filtered_reasons:
        assert reason in filtered_reasons, f"Expected filtered reason {reason!r} for {sample_path.name}"


@pytest.mark.parametrize(
    ("keyword", "region"),
    KNOWN_SAMPLE_CASES,
    ids=[f"{region}-{keyword}" for keyword, region in KNOWN_SAMPLE_CASES],
)
def test_all_known_real_samples_standardize_without_pipeline_errors(keyword: str, region: str) -> None:
    sample_path = find_sample(keyword)

    discovery = discover_workbook(sample_path)
    extraction = extract_header_structure(sample_path)
    result = standardize_workbook(sample_path, region=region)

    assert discovery.selected_sheet_name
    assert extraction.columns
    assert extraction.data_start_row >= max(extraction.header_rows)
    assert result.records or result.filtered_rows
    assert result.raw_header_signature
