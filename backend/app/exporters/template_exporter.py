from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

from openpyxl import Workbook, load_workbook
from openpyxl.formula.translate import Translator
from openpyxl.utils import get_column_letter
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
    sheet = workbook[workbook.sheetnames[0]]
    _rewrite_sheet_in_place(
        sheet,
        template_row=SALARY_DATA_START_ROW,
        records=records,
        value_builder=_salary_row_values,
    )


def _rewrite_tool_sheet(workbook: Workbook, records: list[NormalizedRecord]) -> None:
    sheet = workbook[workbook.sheetnames[0]]
    _rewrite_sheet_in_place(
        sheet,
        template_row=TOOL_DATA_START_ROW,
        records=records,
        value_builder=_tool_row_values,
    )


def _rewrite_sheet_in_place(
    sheet: Worksheet,
    *,
    template_row: int,
    records: list[NormalizedRecord],
    value_builder,
) -> None:
    row_values = [value_builder(record) for record in records]
    template_snapshot = _snapshot_row(sheet, template_row)
    target_last_row = max(sheet.max_row, template_row + len(records) - 1)

    for target_row in range(template_row, target_last_row + 1):
        _apply_row_snapshot(sheet, template_snapshot, source_row=template_row, target_row=target_row)
        values = row_values[target_row - template_row] if target_row - template_row < len(row_values) else None
        _populate_output_row(sheet, template_snapshot, target_row=target_row, values=values)


def _snapshot_row(sheet: Worksheet, row_number: int) -> dict[str, object]:
    row_dimension = copy(sheet.row_dimensions[row_number]) if row_number in sheet.row_dimensions else None
    cells = []
    for column_index in range(1, sheet.max_column + 1):
        cell = sheet.cell(row=row_number, column=column_index)
        cells.append(
            {
                'column_index': column_index,
                'value': cell.value,
                'style': copy(cell._style) if cell.has_style else None,
                'font': copy(cell.font),
                'fill': copy(cell.fill),
                'border': copy(cell.border),
                'alignment': copy(cell.alignment),
                'number_format': cell.number_format,
                'protection': copy(cell.protection),
            }
        )
    return {'row_dimension': row_dimension, 'cells': cells}


def _apply_row_snapshot(
    sheet: Worksheet,
    snapshot: dict[str, object],
    *,
    source_row: int,
    target_row: int,
) -> None:
    row_dimension = snapshot['row_dimension']
    if row_dimension is not None:
        sheet.row_dimensions[target_row] = copy(row_dimension)

    for cell_snapshot in snapshot['cells']:
        column_index = cell_snapshot['column_index']
        target_cell = sheet.cell(row=target_row, column=column_index)
        value = cell_snapshot['value']
        if isinstance(value, str) and value.startswith('=') and target_row != source_row:
            origin = f"{get_column_letter(column_index)}{source_row}"
            destination = f"{get_column_letter(column_index)}{target_row}"
            value = Translator(value, origin=origin).translate_formula(destination)
        target_cell.value = value
        target_cell.font = copy(cell_snapshot['font'])
        target_cell.fill = copy(cell_snapshot['fill'])
        target_cell.border = copy(cell_snapshot['border'])
        target_cell.alignment = copy(cell_snapshot['alignment'])
        target_cell.number_format = cell_snapshot['number_format']
        target_cell.protection = copy(cell_snapshot['protection'])
        if cell_snapshot['style'] is not None:
            target_cell._style = copy(cell_snapshot['style'])


def _populate_output_row(
    sheet: Worksheet,
    snapshot: dict[str, object],
    *,
    target_row: int,
    values: list[object] | None,
) -> None:
    cell_snapshots = snapshot['cells']
    for cell_snapshot in cell_snapshots:
        column_index = cell_snapshot['column_index']
        template_value = cell_snapshot['value']
        is_formula = isinstance(template_value, str) and template_value.startswith('=')
        uses_external_reference = is_formula and '[' in template_value
        target_cell = sheet.cell(row=target_row, column=column_index)

        if values is None:
            if not (is_formula and not uses_external_reference):
                target_cell.value = None
            continue

        if column_index > len(values):
            continue
        if is_formula and not uses_external_reference:
            continue
        target_cell.value = values[column_index - 1]


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


def _amount(value: Decimal | None) -> Decimal:
    return value if value is not None else Decimal('0')


def _region_label(value: str | None) -> str:
    if value is None:
        return ''
    return REGION_LABELS.get(value, value)
