from __future__ import annotations

from pathlib import Path
from decimal import Decimal

import pytest

from backend.app.core.config import ROOT_DIR
from backend.app.services import build_normalized_models, standardize_workbook


SAMPLES_DIR = ROOT_DIR / 'data' / 'samples'


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Sample containing {keyword!r} was not found in {SAMPLES_DIR}.')


def test_standardize_workbook_on_real_guangzhou_sample() -> None:
    sample_path = find_sample('\u5e7f\u5206')

    result = standardize_workbook(sample_path, region='guangzhou')

    first = result.records[0]
    assert result.sheet_name == 'sheet1'
    assert first.source_row_number == 9
    assert first.values['person_name']
    assert first.values['id_number']
    assert first.values['social_security_number']
    assert first.values['billing_period'] == '2026-02'
    assert first.values['company_total_amount'] is not None
    assert first.values['personal_total_amount'] is not None
    assert first.values['pension_company'] is not None
    assert first.values['medical_maternity_company'] is not None
    assert first.values['injury_company'] is not None
    assert first.raw_values['\u5e8f\u53f7'] == 1
    assert first.unmapped_values['\u5e8f\u53f7'] == 1


def test_standardize_workbook_on_real_hangzhou_sample() -> None:
    sample_path = find_sample('\u676d\u5dde\u805a\u53d8')

    result = standardize_workbook(sample_path, region='hangzhou')

    first = result.records[0]
    assert len(result.records) > 0
    assert any(row.reason == 'summary_total' for row in result.filtered_rows)
    assert first.values['person_name']
    assert first.values['id_number']
    assert first.values['pension_company'] is not None
    assert first.values['pension_personal'] is not None
    assert first.values['medical_company'] is not None
    assert first.values['medical_personal'] is not None
    assert first.values['unemployment_company'] is not None
    assert first.values['injury_company'] is not None
    assert '\u5408\u8ba1' in first.unmapped_values


def test_standardize_workbook_on_real_xiamen_sample() -> None:
    sample_path = find_sample('\u53a6\u95e8202602\u793e\u4fdd\u8d26\u5355.xlsx')

    result = standardize_workbook(sample_path, region='xiamen')

    first = result.records[0]
    assert len(result.records) > 0
    assert any(row.row_number == 37 and row.reason == 'summary_total' for row in result.filtered_rows)
    assert first.values['billing_period'] == '2026-02'
    assert first.values['period_start'] == '2026-02-01'
    assert first.values['period_end'] == '2026-02-28'
    assert first.values['total_amount'] is not None
    assert first.values['company_total_amount'] is not None
    assert first.values['personal_total_amount'] is not None
    assert first.values['late_fee'] == Decimal('0')
    assert first.values['interest'] == Decimal('0')
    assert '\u53c2\u4fdd\u4eba\u5458\u8eab\u4efd' in first.unmapped_values


def test_standardize_workbook_on_real_shenzhen_sample() -> None:
    sample_path = find_sample('\u6df1\u5733\u521b\u9020\u6b22\u4e50')

    result = standardize_workbook(sample_path, region='shenzhen')

    first = result.records[0]
    filtered_reasons = {(row.reason, row.first_value) for row in result.filtered_rows}
    assert ('summary_subtotal', '\u5c0f\u8ba1') in filtered_reasons
    assert ('group_header', '\u9000\u4f11\u4eba\u5458') in filtered_reasons
    assert ('group_header', '\u5bb6\u5c5e\u7edf\u7b79\u4eba\u5458') in filtered_reasons
    assert first.source_row_number == 4
    assert first.values['total_amount'] is not None
    assert first.values['company_total_amount'] is not None
    assert first.values['personal_total_amount'] is not None
    assert first.values['supplementary_pension_company'] is not None
    assert '\u57fa\u672c\u517b\u8001\u4fdd\u9669\uff08\u5355\u4f4d\uff09 / \u8d39\u7387' in first.unmapped_values


def test_standardize_workbook_on_real_wuhan_sample() -> None:
    sample_path = find_sample('\u6b66\u6c49')

    result = standardize_workbook(sample_path, region='wuhan')

    first = result.records[0]
    assert len(result.records) == 1
    assert any(row.row_number == 4 and row.reason == 'summary_total' for row in result.filtered_rows)
    assert first.values['person_name']
    assert first.values['payment_base'] is not None
    assert first.values['payment_salary'] is not None
    assert first.values['pension_company'] is not None
    assert first.values['pension_personal'] is not None
    assert first.values['medical_company'] is not None
    assert first.values['medical_personal'] is not None


def test_standardize_workbook_on_real_changsha_sample() -> None:
    sample_path = find_sample('\u957f\u6c99')

    result = standardize_workbook(sample_path, region='changsha')

    first = result.records[0]
    assert result.sheet_name == 'Sheet4'
    assert first.source_row_number == 5
    assert first.values['person_name']
    assert first.values['pension_company'] is not None
    assert first.values['medical_company'] is not None
    assert first.values['unemployment_personal'] is not None
    assert first.values['large_medical_personal'] is not None
    assert first.values['total_amount'] is not None


def test_build_normalized_models_preserves_provenance() -> None:
    sample_path = find_sample('\u5e7f\u5206')

    result = standardize_workbook(sample_path, region='guangzhou')
    models = build_normalized_models(result, batch_id='batch-1', source_file_id='source-1')

    assert models
    assert models[0].batch_id == 'batch-1'
    assert models[0].source_file_id == 'source-1'
    assert models[0].source_file_name == sample_path.name
    assert models[0].raw_sheet_name == 'sheet1'
    assert models[0].raw_header_signature == result.raw_header_signature
    assert models[0].raw_payload is not None
    assert models[0].raw_payload['raw_values']['\u59d3\u540d'] == result.records[0].values['person_name']
