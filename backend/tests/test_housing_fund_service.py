from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import Workbook

from backend.app.core.config import ROOT_DIR
from backend.app.services.housing_fund_service import standardize_housing_fund_workbook

SAMPLES_DIR = ROOT_DIR / 'data' / 'samples' / '\u516c\u79ef\u91d1'


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Sample containing {keyword!r} was not found in {SAMPLES_DIR}.')


def test_standardize_housing_fund_workbook_shenzhen_derives_company_and_personal_amounts() -> None:
    sample = find_sample('\u6df1\u5733\u521b\u9020\u6b22\u4e50')
    result = standardize_housing_fund_workbook(sample, region='shenzhen', company_name='\u521b\u9020\u6b22\u4e50')

    first = result.records[0]
    assert result.sheet_name == '\u5355\u7b14\u7f34\u5b58\u6e05\u5355'
    assert first.values['person_name'] == '\u5f20\u826f'
    assert first.values['id_number'] == '36232919941212061X'
    assert first.values['housing_fund_base'] == Decimal('3500')
    assert first.values['housing_fund_personal'] == Decimal('175.00')
    assert first.values['housing_fund_company'] == Decimal('175.00')
    assert first.values['housing_fund_total'] == Decimal('350')


def test_standardize_housing_fund_workbook_hangzhou_reads_explicit_amounts() -> None:
    sample = find_sample('\u676d\u5dde\u805a\u53d8')
    result = standardize_housing_fund_workbook(sample, region='hangzhou', company_name='\u676d\u5dde\u805a\u53d8')

    first = result.records[0]
    assert first.values['person_name'] == '\u738b\u5353'
    assert first.values['housing_fund_account'] == '100202102900'
    assert first.values['housing_fund_personal'] == Decimal('175.00')
    assert first.values['housing_fund_company'] == Decimal('175.00')
    assert first.values['housing_fund_total'] == Decimal('350.00')


def test_standardize_housing_fund_workbook_guangzhou_reads_account_and_company_name() -> None:
    sample = find_sample('\u5e7f\u5206')
    result = standardize_housing_fund_workbook(sample, region='guangzhou')

    first = result.records[0]
    assert first.values['person_name']
    assert first.values['housing_fund_account']
    assert first.values['company_name']
    assert first.values['housing_fund_personal'] is not None
    assert first.values['housing_fund_company'] is not None


def test_standardize_housing_fund_workbook_guangzhou_filters_footer_rows() -> None:
    sample = find_sample('??')
    result = standardize_housing_fund_workbook(sample, region='guangzhou')

    footer_tokens = ('????', '????', '????', '???')
    assert result.records
    assert all(
        not any(token in str(record.values.get('person_name', '')) for token in footer_tokens)
        for record in result.records
    )


def test_standardize_housing_fund_workbook_changsha_reads_total_and_period() -> None:
    sample = find_sample('\u957f\u6c99')
    result = standardize_housing_fund_workbook(sample, region='changsha', company_name='\u957f\u6c99\u793a\u4f8b\u516c\u53f8')

    first = result.records[0]
    assert result.sheet_name.strip() == '\u88681'
    assert first.values['person_name'] == '\u718a\u745b'
    assert first.values['billing_period'] == '2026-02'
    assert first.values['housing_fund_personal'] == Decimal('175')
    assert first.values['housing_fund_company'] == Decimal('175')
    assert first.values['housing_fund_total'] == Decimal('350')


def test_standardize_housing_fund_workbook_wuhan_two_level_headers() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = '武汉202602公积金台账'
    sheet.append(
        [
            '序号',
            '个人公积金账号',
            '职工姓名',
            '摘要',
            '月均工资',
            '新开户、启封本月应缴存额增加',
            None,
            None,
            '销户、封存本月应缴存额减少',
            None,
            None,
        ]
    )
    sheet.append([None, None, None, None, None, '合计', '个人', '单位', '合计', '个人', '单位'])
    sheet.append([1, '847209617', '崔亚鑫', '202602汇缴登记', 2400, 240, 120, 120, 0, 0, 0])
    sheet.append(['本页小计', None, None, None, None, 240, 120, 120, 0, 0, 0])
    sheet.append(['合计', None, None, None, None, 240, 120, 120, 0, 0, 0])

    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()

    temp_path = ROOT_DIR / '.test_artifacts' / 'housing_fund_service' / 'wuhan_two_level_headers.xlsx'
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_bytes(buffer.getvalue())

    result = standardize_housing_fund_workbook(temp_path, region='wuhan', company_name='武汉示例公司')

    assert result.sheet_name == '武汉202602公积金台账'
    assert len(result.records) == 1
    first = result.records[0]
    assert first.values['person_name'] == '崔亚鑫'
    assert first.values['housing_fund_account'] == '847209617'
    assert first.values['housing_fund_base'] == Decimal('2400')
    assert first.values['housing_fund_personal'] == Decimal('120')
    assert first.values['housing_fund_company'] == Decimal('120')
    assert first.values['housing_fund_total'] == Decimal('240')
