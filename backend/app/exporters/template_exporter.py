from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
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
    'guangzhou': '\u5e7f\u5dde',
    'hangzhou': '\u676d\u5dde',
    'xiamen': '\u53a6\u95e8',
    'shenzhen': '\u6df1\u5733',
    'wuhan': '\u6b66\u6c49',
    'changsha': '\u957f\u6c99',
}

SALARY_HEADERS = [
    '\u5458\u5de5\u59d3\u540d', '\u5de5\u53f7', '\u4e2a\u4eba\u533b\u7597\u4fdd\u9669', '\u4e2a\u4eba\u5931\u4e1a\u4fdd\u9669', '\u4e2a\u4eba\u5927\u75c5\u533b\u7597', '\u4e2a\u4eba\u6b8b\u75be\u4fdd\u969c\u91d1', '\u4e2a\u4eba\u517b\u8001\u4fdd\u9669', '\u4e2a\u4eba\u516c\u79ef\u91d1',
    '\u516c\u53f8\u517b\u8001\u4fdd\u9669', '\u516c\u53f8\u533b\u7597\u4fdd\u9669', '\u516c\u53f8\u5931\u4e1a\u4fdd\u9669', '\u516c\u53f8\u5de5\u4f24\u4fdd\u9669', '\u516c\u53f8\u751f\u80b2\u4fdd\u9669', '\u516c\u53f8\u5927\u75c5\u533b\u7597', '\u516c\u53f8\u6b8b\u75be\u4fdd\u969c\u91d1', '\u516c\u53f8\u516c\u79ef\u91d1',
    '\u4e2a\u4eba\u793e\u4fdd\u627f\u62c5\u989d', '\u4e2a\u4eba\u516c\u79ef\u91d1\u627f\u62c5\u989d',
]

TOOL_HEADERS = [
    '\u4e3b\u4f53', '\u533a\u57df', '\u5458\u5de5\u59d3\u540d\uff08\u8f85\u52a9\uff09', '\u8eab\u4efd\u8bc1', '\u5de5\u53f7', None, '\u5458\u5de5\u59d3\u540d', '\u5de5\u53f7', '\u4e2a\u4eba\u533b\u7597\u4fdd\u9669', '\u4e2a\u4eba\u5931\u4e1a\u4fdd\u9669', '\u4e2a\u4eba\u5927\u75c5\u533b\u7597',
    '\u4e2a\u4eba\u6b8b\u75be\u4fdd\u969c\u91d1', '\u4e2a\u4eba\u517b\u8001\u4fdd\u9669', '\u4e2a\u4eba\u516c\u79ef\u91d1', '\u516c\u53f8\u517b\u8001\u4fdd\u9669', '\u516c\u53f8\u533b\u7597\u4fdd\u9669', '\u516c\u53f8\u5931\u4e1a\u4fdd\u9669', '\u516c\u53f8\u5de5\u4f24\u4fdd\u9669', '\u516c\u53f8\u751f\u80b2\u4fdd\u9669',
    '\u516c\u53f8\u5927\u75c5\u533b\u7597', '\u516c\u53f8\u6b8b\u75be\u4fdd\u969c\u91d1', '\u516c\u53f8\u516c\u79ef\u91d1', '\u4e2a\u4eba\u793e\u4fdd\u627f\u62c5\u989d', '\u4e2a\u4eba\u516c\u79ef\u91d1\u627f\u62c5\u989d', None, None, '\u4e2a\u4eba\u793e\u4fdd\u5e94\u7f34\u7eb3\u603b\u989d', '\u4e2a\u4eba\u627f\u62c5\u68c0\u9a8c',
    '\u4e2a\u4eba\u793e\u4fdd\u68c0\u9a8c', '\u4e2a\u4eba\u516c\u79ef\u91d1', '\u4e2a\u4eba+\u5355\u4f4d\u5408\u8ba1\u627f\u62c5\u603b\u989d', None, '\u5355\u4f4d\u627f\u62c5\u793e\u4fdd', '\u516c\u53f8\u627f\u62c5\u68c0\u9a8c', '\u68c0\u9a8c\u503c', '\u5355\u4f4d\u627f\u62c5\u516c\u79ef\u91d1',
    '\u5355\u4f4d\u793e\u4fdd+\u516c\u79ef\u91d1\u5408\u8ba1\u627f\u62c5\u603b\u989d', None, None, '\u793e\u4fdd\uff1a\u4e2a\u4eba+\u5355\u4f4d', '\u516c\u79ef\u91d1\uff1a\u4e2a\u4eba+\u5355\u4f4d', '\u4e2a\u4eba+\u5355\u4f4d\u5408\u8ba1',
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
    personal_housing, company_housing, _housing_total = _resolved_housing_fund_values(record)

    return [
        record.person_name or '',
        record.employee_id or '',
        personal_medical,
        personal_unemployment,
        personal_large_medical,
        Decimal('0'),
        personal_pension,
        personal_housing,
        company_pension,
        company_medical,
        company_unemployment,
        company_injury,
        company_maternity,
        company_large_medical,
        Decimal('0'),
        company_housing,
        personal_social_total,
        personal_housing,
    ]


def _tool_row_values(record: NormalizedRecord) -> list[object]:
    salary_values = _salary_row_values(record)
    personal_social_total = _amount(record.personal_total_amount)
    personal_housing_fund, company_housing_fund, _housing_total = _resolved_housing_fund_values(record)
    company_social_total = sum(salary_values[8:15], Decimal('0'))
    personal_social_due = sum(salary_values[2:7], Decimal('0'))
    personal_total_with_company = personal_social_due + personal_social_total + personal_housing_fund
    social_grand_total = personal_social_due + personal_social_total + company_social_total
    housing_grand_total = personal_housing_fund + company_housing_fund
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
        personal_housing_fund,
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


def _resolved_housing_fund_values(record: NormalizedRecord) -> tuple[Decimal, Decimal, Decimal]:
    personal = _amount(record.housing_fund_personal)
    company = _amount(record.housing_fund_company)
    total = _amount(record.housing_fund_total)
    quant = Decimal('0.01')

    if total == 0:
        total = personal + company
    if personal == 0 and company == 0 and total != 0:
        personal = (total / Decimal('2')).quantize(quant, rounding=ROUND_HALF_UP)
        company = (total - personal).quantize(quant, rounding=ROUND_HALF_UP)
    elif personal == 0 and total != 0 and company != 0:
        personal = (total - company).quantize(quant, rounding=ROUND_HALF_UP)
    elif company == 0 and total != 0 and personal != 0:
        company = (total - personal).quantize(quant, rounding=ROUND_HALF_UP)

    if total == 0:
        total = personal + company
    return personal, company, total


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

    pattern = '*\u85aa\u916c*.xlsx' if template_type == TemplateType.SALARY else '*\u6700\u7ec8\u7248*.xlsx'
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
