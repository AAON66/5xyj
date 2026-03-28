from __future__ import annotations

from decimal import Decimal
from typing import Optional

from openpyxl import Workbook

from backend.app.models.normalized_record import NormalizedRecord

from backend.app.exporters.export_utils import (
    _build_housing_burden_context,
    _build_social_burden_context,
    _region_label,
    _resolved_housing_fund_values,
    _rewrite_sheet_in_place,
)
from backend.app.exporters.salary_exporter import _salary_row_values

TOOL_SHEET_HEADER_ROW = 6
TOOL_DATA_START_ROW = 7

TOOL_HEADERS = [
    '\u4e3b\u4f53', '\u533a\u57df', '\u5458\u5de5\u59d3\u540d\uff08\u8f85\u52a9\uff09', '\u8eab\u4efd\u8bc1', '\u5de5\u53f7', None, '\u5458\u5de5\u59d3\u540d', '\u5de5\u53f7', '\u4e2a\u4eba\u533b\u7597\u4fdd\u9669', '\u4e2a\u4eba\u5931\u4e1a\u4fdd\u9669', '\u4e2a\u4eba\u5927\u75c5\u533b\u7597',
    '\u4e2a\u4eba\u6b8b\u75be\u4fdd\u969c\u91d1', '\u4e2a\u4eba\u517b\u8001\u4fdd\u9669', '\u4e2a\u4eba\u516c\u79ef\u91d1', '\u516c\u53f8\u517b\u8001\u4fdd\u9669', '\u516c\u53f8\u533b\u7597\u4fdd\u9669', '\u516c\u53f8\u5931\u4e1a\u4fdd\u9669', '\u516c\u53f8\u5de5\u4f24\u4fdd\u9669', '\u516c\u53f8\u751f\u80b2\u4fdd\u9669',
    '\u516c\u53f8\u5927\u75c5\u533b\u7597', '\u516c\u53f8\u6b8b\u75be\u4fdd\u969c\u91d1', '\u516c\u53f8\u516c\u79ef\u91d1', '\u4e2a\u4eba\u793e\u4fdd\u627f\u62c5\u989d', '\u4e2a\u4eba\u516c\u79ef\u91d1\u627f\u62c5\u989d', None, None, '\u4e2a\u4eba\u793e\u4fdd\u5e94\u7f34\u7eb3\u603b\u989d', '\u4e2a\u4eba\u627f\u62c5\u68c0\u9a8c',
    '\u4e2a\u4eba\u793e\u4fdd\u68c0\u9a8c', '\u4e2a\u4eba\u516c\u79ef\u91d1', '\u4e2a\u4eba+\u5355\u4f4d\u5408\u8ba1\u627f\u62c5\u603b\u989d', None, '\u5355\u4f4d\u627f\u62c5\u793e\u4fdd', '\u516c\u53f8\u627f\u62c5\u68c0\u9a8c', '\u68c0\u9a8c\u503c', '\u5355\u4f4d\u627f\u62c5\u516c\u79ef\u91d1',
    '\u5355\u4f4d\u793e\u4fdd+\u516c\u79ef\u91d1\u5408\u8ba1\u627f\u62c5\u603b\u989d', None, None, '\u793e\u4fdd\uff1a\u4e2a\u4eba+\u5355\u4f4d', '\u516c\u79ef\u91d1\uff1a\u4e2a\u4eba+\u5355\u4f4d', '\u4e2a\u4eba+\u5355\u4f4d\u5408\u8ba1',
]


def _rewrite_tool_sheet(workbook: Workbook, records: list[NormalizedRecord]) -> None:
    sheet = workbook[workbook.sheetnames[0]]
    social_burden_context = _build_social_burden_context(records)
    housing_burden_context = _build_housing_burden_context(records)
    _rewrite_sheet_in_place(
        sheet,
        template_row=TOOL_DATA_START_ROW,
        records=records,
        value_builder=lambda record: _tool_row_values(record, social_burden_context, housing_burden_context),
    )


def _tool_row_values(
    record: NormalizedRecord,
    social_burden_context: dict[str, tuple[Decimal, ...]] | None = None,
    housing_burden_context: dict[str, tuple[Decimal, ...]] | None = None,
) -> list[object]:
    salary_values = _salary_row_values(record, social_burden_context, housing_burden_context)
    personal_social_burden = salary_values[16]
    personal_housing_fund, company_housing_fund, _housing_total = _resolved_housing_fund_values(record)
    company_social_total = sum(salary_values[8:15], Decimal('0'))
    personal_social_due = sum(salary_values[2:7], Decimal('0'))
    personal_total_with_company = personal_social_due + personal_social_burden + personal_housing_fund
    social_grand_total = personal_social_due + personal_social_burden + company_social_total
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
