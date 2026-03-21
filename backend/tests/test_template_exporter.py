from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import load_workbook

from backend.app.core.config import ROOT_DIR, get_settings
from backend.app.exporters import export_dual_templates
from backend.app.services import build_normalized_models, standardize_workbook


ARTIFACTS_ROOT = ROOT_DIR / '.test_artifacts' / 'template_exporter'
DESKTOP_ROOT = Path.home() / 'Desktop' / '202602社保公积金台账' / '202602社保公积金汇总'


def find_template(keyword: str) -> Path:
    if not DESKTOP_ROOT.exists():
        pytest.skip(f'Template root was not found: {DESKTOP_ROOT}')
    for path in sorted(DESKTOP_ROOT.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Template containing {keyword!r} was not found in {DESKTOP_ROOT}.')


def find_sample(keyword: str) -> Path:
    samples_dir = ROOT_DIR / 'data' / 'samples'
    for path in sorted(samples_dir.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Sample containing {keyword!r} was not found in {samples_dir}.')


def test_export_dual_templates_writes_both_template_outputs() -> None:
    salary_template = find_template('薪酬')
    tool_template = find_template('最终版')
    sample_path = find_sample('深圳创造欢乐')

    standardized = standardize_workbook(sample_path, region='shenzhen', company_name='创造欢乐')
    trimmed = type(standardized)(
        source_file=standardized.source_file,
        sheet_name=standardized.sheet_name,
        raw_header_signature=standardized.raw_header_signature,
        records=standardized.records[:2],
        filtered_rows=standardized.filtered_rows,
        unmapped_headers=standardized.unmapped_headers,
    )
    records = build_normalized_models(trimmed, batch_id='batch-1', source_file_id='source-1')
    records[0].employee_id = '01620'
    records[1].employee_id = '01831'
    records[0].housing_fund_personal = records[0].housing_fund_personal or records[0].personal_total_amount
    records[0].housing_fund_company = records[0].housing_fund_company or records[0].personal_total_amount
    records[0].housing_fund_total = records[0].housing_fund_personal + records[0].housing_fund_company

    output_dir = ARTIFACTS_ROOT / 'successful_export'
    output_dir.mkdir(parents=True, exist_ok=True)

    result = export_dual_templates(
        records,
        output_dir=output_dir,
        salary_template_path=salary_template,
        final_tool_template_path=tool_template,
        export_prefix='match_batch',
    )

    assert result.status == 'completed'
    salary_artifact = next(item for item in result.artifacts if item.template_type == 'salary')
    tool_artifact = next(item for item in result.artifacts if item.template_type == 'final_tool')
    assert salary_artifact.status == 'completed'
    assert tool_artifact.status == 'completed'

    salary_wb = load_workbook(salary_artifact.file_path, data_only=False)
    salary_sheet = salary_wb[salary_wb.sheetnames[0]]
    assert salary_sheet['A2'].value == records[0].person_name
    assert salary_sheet['B2'].value == '01620'
    assert float(salary_sheet['C2'].value) == float(records[0].medical_personal)
    assert float(salary_sheet['I2'].value) == float(records[0].pension_company + records[0].supplementary_pension_company)
    assert float(salary_sheet['H2'].value) == float(records[0].housing_fund_personal)
    assert float(salary_sheet['P2'].value) == float(records[0].housing_fund_company)
    assert float(salary_sheet['Q2'].value) == float(records[0].personal_total_amount)
    salary_wb.close()

    tool_wb = load_workbook(tool_artifact.file_path, data_only=False)
    tool_sheet = tool_wb[tool_wb.sheetnames[0]]
    assert tool_sheet['A7'].value == '创造欢乐'
    assert tool_sheet['B7'].value == '深圳'
    assert tool_sheet['D7'].value == records[0].id_number
    assert tool_sheet['E7'].value == '01620'
    assert float(tool_sheet['O7'].value) == float(records[0].pension_company + records[0].supplementary_pension_company)
    assert float(tool_sheet['N7'].value) == float(records[0].housing_fund_personal)
    assert float(tool_sheet['V7'].value) == float(records[0].housing_fund_company)
    assert float(tool_sheet['W7'].value) == float(records[0].personal_total_amount)
    assert tool_sheet['AA7'].data_type == 'f'
    assert str(tool_sheet['AA7'].value).startswith('=')
    assert tool_sheet['AO7'].data_type == 'f'
    assert str(tool_sheet['AO7'].value).startswith('=')
    tool_wb.close()


def test_export_dual_templates_marks_overall_failure_when_any_template_is_missing() -> None:
    salary_template = find_template('薪酬')
    sample_path = find_sample('深圳创造欢乐')
    standardized = standardize_workbook(sample_path, region='shenzhen', company_name='创造欢乐')
    trimmed = type(standardized)(
        source_file=standardized.source_file,
        sheet_name=standardized.sheet_name,
        raw_header_signature=standardized.raw_header_signature,
        records=standardized.records[:1],
        filtered_rows=standardized.filtered_rows,
        unmapped_headers=standardized.unmapped_headers,
    )
    records = build_normalized_models(trimmed, batch_id='batch-1', source_file_id='source-1')
    records[0].employee_id = '01620'

    output_dir = ARTIFACTS_ROOT / 'failed_export'
    output_dir.mkdir(parents=True, exist_ok=True)

    result = export_dual_templates(
        records,
        output_dir=output_dir,
        salary_template_path=salary_template,
        final_tool_template_path=output_dir / 'missing.xlsx',
        export_prefix='missing_template',
    )

    assert result.status == 'failed'
    assert next(item for item in result.artifacts if item.template_type == 'salary').status == 'completed'
    failed_tool = next(item for item in result.artifacts if item.template_type == 'final_tool')
    assert failed_tool.status == 'failed'
    assert failed_tool.error_message
