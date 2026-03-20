from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from backend.app.core.config import get_settings
from backend.app.models.enums import TemplateType
from backend.app.models.normalized_record import NormalizedRecord

SALARY_SHEET_HEADER_ROW = 1
SALARY_DATA_START_ROW = 2
TOOL_SHEET_HEADER_ROW = 6
TOOL_DATA_START_ROW = 7

REGION_LABELS = {
    'guangzhou': '广州',
    'hangzhou': '杭州',
    'xiamen': '厦门',
    'shenzhen': '深圳',
    'wuhan': '武汉',
    'changsha': '长沙',
}

SALARY_HEADERS = [
    '员工姓名', '工号', '个人医疗保险', '个人失业保险', '个人大病医疗', '个人残疾保障金', '个人养老保险', '个人公积金',
    '公司养老保险', '公司医疗保险', '公司失业保险', '公司工伤保险', '公司生育保险', '公司大病医疗', '公司残疾保障金', '公司公积金',
    '个人社保承担额', '个人公积金承担额',
]

TOOL_HEADERS = [
    '主体', '区域', '员工姓名（辅助）', '身份证', '工号', None, '员工姓名', '工号', '个人医疗保险', '个人失业保险', '个人大病医疗',
    '个人残疾保障金', '个人养老保险', '个人公积金', '公司养老保险', '公司医疗保险', '公司失业保险', '公司工伤保险', '公司生育保险',
    '公司大病医疗', '公司残疾保障金', '公司公积金', '个人社保承担额', '个人公积金承担额', None, None, '个人社保应缴纳总额', '个人承担检验',
    '个人社保检验', '个人公积金', '个人+单位合计承担总额', None, '单位承担社保', '公司承担检验', '检验值', '单位承担公积金',
    '单位社保+公积金合计承担总额', None, None, '社保：个人+单位', '公积金：个人+单位', '个人+单位合计',
]


class ExportServiceError(Exception):
    pass


@dataclass(slots=True)
class ExportArtifactResult:
    template_type: str
    status: str
    file_path: str | None
    error_message: str | None
    row_count: int = 0


@dataclass(slots=True)
class DualTemplateExportResult:
    status: str
    artifacts: list[ExportArtifactResult]


def export_dual_templates(
    records: Iterable[NormalizedRecord],
    *,
    output_dir: str | Path | None = None,
    salary_template_path: str | Path | None = None,
    final_tool_template_path: str | Path | None = None,
    export_prefix: str | None = None,
) -> DualTemplateExportResult:
    normalized_records = list(records)
    settings = get_settings()
    output_root = Path(output_dir) if output_dir else settings.outputs_path
    output_root.mkdir(parents=True, exist_ok=True)

    prefix = export_prefix or 'batch'
    template_inputs = [
        (TemplateType.SALARY, salary_template_path, output_root / f'{prefix}_{TemplateType.SALARY.value}.xlsx'),
        (TemplateType.FINAL_TOOL, final_tool_template_path, output_root / f'{prefix}_{TemplateType.FINAL_TOOL.value}.xlsx'),
    ]

    artifacts: list[ExportArtifactResult] = []
    for template_type, explicit_path, output_path in template_inputs:
        try:
            template_path = _resolve_template_path(explicit_path, template_type)
        except ExportServiceError as exc:
            artifacts.append(ExportArtifactResult(template_type.value, 'failed', None, str(exc), 0))
            continue
        artifacts.append(_export_template_variant(template_type, template_path, output_path, normalized_records))

    overall_status = 'completed' if all(item.status == 'completed' for item in artifacts) else 'failed'
    return DualTemplateExportResult(status=overall_status, artifacts=artifacts)


def _export_template_variant(
    template_type: TemplateType,
    template_path: Path,
    output_path: Path,
    records: list[NormalizedRecord],
) -> ExportArtifactResult:
    try:
        workbook = load_workbook(template_path)
        if template_type == TemplateType.SALARY:
            _rewrite_salary_sheet(workbook, records)
        else:
            _rewrite_tool_sheet(workbook, records)
        workbook.save(output_path)
        workbook.close()
        return ExportArtifactResult(template_type.value, 'completed', str(output_path), None, len(records))
    except Exception as exc:
        return ExportArtifactResult(template_type.value, 'failed', None, str(exc), 0)


def _rewrite_salary_sheet(workbook: Workbook, records: list[NormalizedRecord]) -> None:
    template_sheet = workbook[workbook.sheetnames[0]]
    new_sheet = workbook.create_sheet(title=f'{template_sheet.title}_export', index=0)
    _copy_sheet_settings(template_sheet, new_sheet, preserve_rows_up_to=SALARY_DATA_START_ROW + 1)
    _copy_header_rows(template_sheet, new_sheet, SALARY_SHEET_HEADER_ROW)

    for offset, record in enumerate(records):
        target_row = SALARY_DATA_START_ROW + offset
        _copy_row_style(template_sheet, new_sheet, SALARY_DATA_START_ROW, target_row, len(SALARY_HEADERS))
        for column_index, value in enumerate(_salary_row_values(record), start=1):
            new_sheet.cell(row=target_row, column=column_index, value=value)

    workbook.remove(template_sheet)
    new_sheet.title = template_sheet.title


def _rewrite_tool_sheet(workbook: Workbook, records: list[NormalizedRecord]) -> None:
    template_sheet = workbook[workbook.sheetnames[0]]
    new_sheet = workbook.create_sheet(title=f'{template_sheet.title}_export', index=0)
    _copy_sheet_settings(template_sheet, new_sheet, preserve_rows_up_to=TOOL_DATA_START_ROW + 1)
    _copy_header_rows(template_sheet, new_sheet, TOOL_SHEET_HEADER_ROW)

    for offset, record in enumerate(records):
        target_row = TOOL_DATA_START_ROW + offset
        _copy_row_style(template_sheet, new_sheet, TOOL_DATA_START_ROW, target_row, len(TOOL_HEADERS))
        for column_index, value in enumerate(_tool_row_values(record), start=1):
            new_sheet.cell(row=target_row, column=column_index, value=value)

    workbook.remove(template_sheet)
    new_sheet.title = template_sheet.title


def _salary_row_values(record: NormalizedRecord) -> list[object]:
    personal_medical = _amount(record.medical_personal)
    personal_unemployment = _amount(record.unemployment_personal)
    personal_large_medical = _amount(record.large_medical_personal)
    personal_pension = _amount(record.pension_personal)
    company_pension = _amount(record.pension_company) + _amount(record.supplementary_pension_company)
    company_medical = _amount(record.medical_maternity_company or record.medical_company)
    company_unemployment = _amount(record.unemployment_company)
    company_injury = _amount(record.injury_company)
    company_maternity = _amount(record.maternity_amount)
    company_large_medical = _amount(record.supplementary_medical_company)
    personal_social_total = _amount(record.personal_total_amount)

    return [
        record.person_name or '',
        record.employee_id or '',
        personal_medical,
        personal_unemployment,
        personal_large_medical,
        Decimal('0'),
        personal_pension,
        Decimal('0'),
        company_pension,
        company_medical,
        company_unemployment,
        company_injury,
        company_maternity,
        company_large_medical,
        Decimal('0'),
        Decimal('0'),
        personal_social_total,
        Decimal('0'),
    ]


def _tool_row_values(record: NormalizedRecord) -> list[object]:
    salary_values = _salary_row_values(record)
    personal_social_total = _amount(record.personal_total_amount)
    personal_housing_fund = Decimal('0')
    company_social_total = sum(salary_values[8:15], Decimal('0'))
    company_housing_fund = Decimal('0')
    personal_social_due = sum(salary_values[2:7], Decimal('0'))
    personal_total_with_company = personal_social_due + personal_social_total + personal_housing_fund + salary_values[7]
    social_grand_total = personal_social_due + personal_social_total + company_social_total
    housing_grand_total = salary_values[7] + company_housing_fund
    overall_total = personal_total_with_company + (company_social_total + company_housing_fund)

    return [
        record.company_name or '',
        _region_label(record.region),
        record.person_name or '',
        record.id_number or '',
        record.employee_id or '',
        None,
        record.person_name or '',
        record.employee_id or '',
        *salary_values[2:],
        None,
        None,
        personal_social_due,
        personal_social_due,
        Decimal('0'),
        salary_values[7],
        personal_total_with_company,
        None,
        company_social_total,
        company_social_total,
        Decimal('0'),
        company_housing_fund,
        company_social_total + company_housing_fund,
        None,
        None,
        social_grand_total,
        housing_grand_total,
        overall_total,
    ]


def _resolve_template_path(template_path: str | Path | None, template_type: TemplateType) -> Path:
    if template_path:
        candidate = Path(template_path)
        if candidate.exists():
            return candidate
        raise ExportServiceError(f'Template path does not exist: {candidate}')

    settings = get_settings()
    configured = settings.salary_template_file if template_type == TemplateType.SALARY else settings.final_tool_template_file
    if configured and configured.exists():
        return configured

    pattern = '*薪酬*.xlsx' if template_type == TemplateType.SALARY else '*最终版*.xlsx'
    matches = sorted(settings.templates_path.glob(pattern))
    if matches:
        return matches[0]
    raise ExportServiceError(f'No template could be resolved for {template_type.value}.')


def _copy_sheet_settings(source: Worksheet, target: Worksheet, *, preserve_rows_up_to: int) -> None:
    target.freeze_panes = source.freeze_panes
    target.sheet_state = source.sheet_state
    target.sheet_format.defaultColWidth = source.sheet_format.defaultColWidth
    target.sheet_format.defaultRowHeight = source.sheet_format.defaultRowHeight
    target.sheet_view.zoomScale = source.sheet_view.zoomScale
    target.page_margins = copy(source.page_margins)
    target.page_setup = copy(source.page_setup)
    target.print_options = copy(source.print_options)
    target.sheet_properties = copy(source.sheet_properties)
    for key, dimension in source.column_dimensions.items():
        target.column_dimensions[key] = copy(dimension)
    for key, dimension in source.row_dimensions.items():
        if key <= preserve_rows_up_to:
            target.row_dimensions[key] = copy(dimension)


def _copy_header_rows(source: Worksheet, target: Worksheet, header_row: int) -> None:
    max_column = source.max_column
    for row_number in range(1, header_row + 1):
        _copy_row_style(source, target, row_number, row_number, max_column)
        for column_index in range(1, max_column + 1):
            source_cell = source.cell(row=row_number, column=column_index)
            target_cell = target.cell(row=row_number, column=column_index, value=source_cell.value)
            _copy_cell_style(source_cell, target_cell)
    for merged_range in source.merged_cells.ranges:
        if merged_range.max_row <= header_row:
            target.merge_cells(str(merged_range))


def _copy_row_style(source: Worksheet, target: Worksheet, source_row: int, target_row: int, max_column: int) -> None:
    if source_row in source.row_dimensions:
        target.row_dimensions[target_row] = copy(source.row_dimensions[source_row])
    for column_index in range(1, max_column + 1):
        source_cell = source.cell(row=source_row, column=column_index)
        target_cell = target.cell(row=target_row, column=column_index)
        _copy_cell_style(source_cell, target_cell)


def _copy_cell_style(source_cell, target_cell) -> None:
    target_cell.font = copy(source_cell.font)
    target_cell.fill = copy(source_cell.fill)
    target_cell.border = copy(source_cell.border)
    target_cell.alignment = copy(source_cell.alignment)
    target_cell.number_format = source_cell.number_format
    target_cell.protection = copy(source_cell.protection)
    if source_cell.has_style:
        target_cell._style = copy(source_cell._style)


def _amount(value: Decimal | None) -> Decimal:
    return value if value is not None else Decimal('0')


def _region_label(value: str | None) -> str:
    if value is None:
        return ''
    return REGION_LABELS.get(value, value)
