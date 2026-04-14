from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from pathlib import Path
import sqlite3

import pytest
from openpyxl import Workbook

from backend.app.core.config import ROOT_DIR
from backend.app.services.housing_fund_service import standardize_housing_fund_workbook

SAMPLES_DIR = ROOT_DIR / 'data' / 'samples' / '\u516c\u79ef\u91d1'
APP_DB = ROOT_DIR / 'data' / 'app.db'


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Sample containing {keyword!r} was not found in {SAMPLES_DIR}.')


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
    assert first.values['billing_period'] == '2026-02'
    assert first.values['housing_fund_account'] == '100202102900'
    assert first.values['housing_fund_personal'] == Decimal('175.00')
    assert first.values['housing_fund_company'] == Decimal('175.00')
    assert first.values['housing_fund_total'] == Decimal('350.00')


def test_standardize_housing_fund_workbook_uploaded_hangzhou_read_only_sheet_access() -> None:
    sample = find_uploaded_sample('杭州聚变202512公积金台账.xlsx')
    result = standardize_housing_fund_workbook(sample, region='hangzhou', company_name='杭州聚变')

    assert result.records
    match = next(record for record in result.records if record.values.get('person_name') == '王卓')
    assert match.values['billing_period'] == '2025-12'
    assert str(match.values['housing_fund_account']) == '100202102900'
    assert match.values['housing_fund_personal'] == Decimal('175.00')
    assert match.values['housing_fund_company'] == Decimal('175.00')


def test_standardize_housing_fund_workbook_uploaded_wuhan_sequence_column_shift() -> None:
    sample = find_uploaded_sample('武汉202512公积金台账.xlsx')
    result = standardize_housing_fund_workbook(sample, region='wuhan', company_name='武汉')

    assert len(result.records) == 3
    match = next(record for record in result.records if record.values.get('person_name') == '崔亚鑫')
    assert str(match.values['housing_fund_account']) == '847209617'
    assert match.values['housing_fund_base'] == Decimal('2210')
    assert match.values['housing_fund_personal'] == Decimal('110.5')
    assert match.values['housing_fund_company'] == Decimal('110.5')
    assert match.values['housing_fund_total'] == Decimal('221')


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


def test_standardize_housing_fund_workbook_xiamen_housing_fund_parse() -> None:
    sample = find_sample('厦门')
    result = standardize_housing_fund_workbook(sample, region='xiamen')

    assert len(result.records) > 0
    first = result.records[0]
    assert first.values.get('person_name')
    # At least one housing fund amount must be present
    assert any(
        first.values.get(key) is not None
        for key in ('housing_fund_base', 'housing_fund_personal', 'housing_fund_company', 'housing_fund_total')
    )
    # No non-detail rows should appear
    non_detail_tokens = ('合计', '小计', '经办网点', '打印日期', '管理中心', '制表人', '说明', '备注', '汇总')
    for record in result.records:
        name = str(record.values.get('person_name', ''))
        assert not any(token in name for token in non_detail_tokens), f'Non-detail row leaked: {name}'


def test_guangzhou_housing_fund_parse() -> None:
    sample = find_sample('广分')
    result = standardize_housing_fund_workbook(sample, region='guangzhou')

    assert len(result.records) > 0
    first = result.records[0]
    assert first.values.get('person_name')
    assert any(
        first.values.get(key) is not None
        for key in ('housing_fund_base', 'housing_fund_personal', 'housing_fund_company', 'housing_fund_total')
    )
    non_detail_tokens = ('合计', '小计', '经办网点', '打印日期', '管理中心', '制表人', '说明', '备注', '汇总')
    for record in result.records:
        name = str(record.values.get('person_name', ''))
        assert not any(token in name for token in non_detail_tokens), f'Non-detail row leaked: {name}'


def test_hangzhou_housing_fund_parse() -> None:
    sample = find_sample('杭州聚变')
    result = standardize_housing_fund_workbook(sample, region='hangzhou')

    assert len(result.records) > 0
    first = result.records[0]
    assert first.values.get('person_name')
    assert any(
        first.values.get(key) is not None
        for key in ('housing_fund_base', 'housing_fund_personal', 'housing_fund_company', 'housing_fund_total')
    )
    non_detail_tokens = ('合计', '小计', '经办网点', '打印日期', '管理中心', '制表人', '说明', '备注', '汇总')
    for record in result.records:
        name = str(record.values.get('person_name', ''))
        assert not any(token in name for token in non_detail_tokens), f'Non-detail row leaked: {name}'


def test_shenzhen_housing_fund_parse() -> None:
    sample = find_sample('深圳创造欢乐')
    result = standardize_housing_fund_workbook(sample, region='shenzhen')

    assert len(result.records) > 0
    first = result.records[0]
    assert first.values.get('person_name')
    assert any(
        first.values.get(key) is not None
        for key in ('housing_fund_base', 'housing_fund_personal', 'housing_fund_company', 'housing_fund_total')
    )
    non_detail_tokens = ('合计', '小计', '经办网点', '打印日期', '管理中心', '制表人', '说明', '备注', '汇总')
    for record in result.records:
        name = str(record.values.get('person_name', ''))
        assert not any(token in name for token in non_detail_tokens), f'Non-detail row leaked: {name}'


@pytest.mark.skipif(
    not any(SAMPLES_DIR.glob('*武汉*')),
    reason='Wuhan housing fund sample not available in samples directory',
)
def test_wuhan_housing_fund_parse() -> None:
    sample = find_sample('武汉')
    result = standardize_housing_fund_workbook(sample, region='wuhan')

    assert len(result.records) > 0
    first = result.records[0]
    assert first.values.get('person_name')
    assert any(
        first.values.get(key) is not None
        for key in ('housing_fund_base', 'housing_fund_personal', 'housing_fund_company', 'housing_fund_total')
    )
    non_detail_tokens = ('合计', '小计', '经办网点', '打印日期', '管理中心', '制表人', '说明', '备注', '汇总')
    for record in result.records:
        name = str(record.values.get('person_name', ''))
        assert not any(token in name for token in non_detail_tokens), f'Non-detail row leaked: {name}'


def test_changsha_housing_fund_parse() -> None:
    sample = find_sample('长沙')
    result = standardize_housing_fund_workbook(sample, region='changsha')

    assert len(result.records) > 0
    first = result.records[0]
    assert first.values.get('person_name')
    assert any(
        first.values.get(key) is not None
        for key in ('housing_fund_base', 'housing_fund_personal', 'housing_fund_company', 'housing_fund_total')
    )
    non_detail_tokens = ('合计', '小计', '经办网点', '打印日期', '管理中心', '制表人', '说明', '备注', '汇总')
    for record in result.records:
        name = str(record.values.get('person_name', ''))
        assert not any(token in name for token in non_detail_tokens), f'Non-detail row leaked: {name}'


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
