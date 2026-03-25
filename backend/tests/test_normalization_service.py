from __future__ import annotations

from pathlib import Path
from decimal import Decimal
import sqlite3

import pytest

from backend.app.core.config import ROOT_DIR
from backend.app.models.enums import SourceFileKind
from backend.app.services import (
    SourceRecordBundle,
    build_normalized_models,
    merge_batch_standardized_records,
    standardize_housing_fund_workbook,
    standardize_workbook,
)


SAMPLES_DIR = ROOT_DIR / 'data' / 'samples'
HOUSING_SAMPLES_DIR = SAMPLES_DIR / '公积金'
APP_DB = ROOT_DIR / 'data' / 'app.db'


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Sample containing {keyword!r} was not found in {SAMPLES_DIR}.')


def find_housing_sample(keyword: str) -> Path:
    for path in sorted(HOUSING_SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Housing sample containing {keyword!r} was not found in {HOUSING_SAMPLES_DIR}.')


def find_uploaded_sample(filename: str) -> Path:
    if not APP_DB.exists():
        pytest.skip(f'Application database was not found at {APP_DB}.')

    connection = sqlite3.connect(APP_DB)
    try:
        row = connection.execute(
            'select file_path from source_files where file_name = ? order by uploaded_at desc limit 1',
            (filename,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        pytest.skip(f'Uploaded sample {filename!r} was not found in {APP_DB}.')

    sample_path = Path(row[0])
    if not sample_path.exists():
        pytest.skip(f'Uploaded sample path no longer exists: {sample_path}.')
    return sample_path


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
    assert first.values['maternity_amount'] == Decimal('31.03')
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


def test_standardize_workbook_on_uploaded_changsha_transactional_sample_maps_large_medical() -> None:
    sample_path = find_uploaded_sample('长沙202602社保账单.xlsx')

    result = standardize_workbook(sample_path, region='changsha')

    match = next(
        record
        for record in result.records
        if record.raw_values.get('征收品目') == '职工大额医疗互助保险(个人缴纳)'
    )
    assert match.values['person_name'] == '余宸瑶'
    assert match.values['total_amount'] == Decimal('15')
    assert match.values['large_medical_personal'] == Decimal('15')


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


def test_merge_batch_standardized_records_merges_name_only_housing_rows_into_hangzhou_social_rows() -> None:
    social_sample = find_sample('\u676d\u5dde\u88c2\u53d8')
    housing_sample = find_housing_sample('\u676d\u5dde\u88c2\u53d8')

    social_result = standardize_workbook(social_sample, region='hangzhou', company_name='\u96f6\u4e00\u88c2\u53d8')
    housing_result = standardize_housing_fund_workbook(housing_sample, region='hangzhou')

    social_names = {record.values.get('person_name') for record in social_result.records}
    target_housing_record = next(
        record
        for record in housing_result.records
        if record.values.get('person_name') in social_names and record.values.get('housing_fund_company') is not None
    )

    merged = merge_batch_standardized_records(
        [
            SourceRecordBundle(
                source_file_id='social-source',
                source_file_name=social_sample.name,
                source_kind=SourceFileKind.SOCIAL_SECURITY.value,
                standardized=social_result,
            ),
            SourceRecordBundle(
                source_file_id='housing-source',
                source_file_name=housing_sample.name,
                source_kind=SourceFileKind.HOUSING_FUND.value,
                standardized=housing_result,
            ),
        ],
        batch_id='batch-merge',
    )

    merged_matches = [record for record in merged if record.person_name == target_housing_record.values.get('person_name')]
    assert len(merged_matches) == 1
    merged_record = merged_matches[0]
    assert merged_record.pension_company is not None
    assert merged_record.housing_fund_company == target_housing_record.values.get('housing_fund_company')
    assert merged_record.housing_fund_personal == target_housing_record.values.get('housing_fund_personal')
