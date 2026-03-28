from __future__ import annotations

from decimal import Decimal
from typing import Optional

from openpyxl import Workbook

from backend.app.models.normalized_record import NormalizedRecord

from backend.app.exporters.export_utils import (
    _amount,
    _build_housing_burden_context,
    _build_social_burden_context,
    _region_label,
    _resolved_company_large_medical,
    _resolved_company_medical,
    _resolved_housing_fund_values,
    _resolved_personal_housing_burden,
    _resolved_personal_large_medical,
    _resolved_personal_social_burden,
    _rewrite_sheet_in_place,
)

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
    # Compute all component values independently (no dependency on salary_exporter)
    personal_medical = _amount(record.medical_personal)
    personal_unemployment = _amount(record.unemployment_personal)
    personal_large_medical = _resolved_personal_large_medical(record)
    personal_disability = Decimal('0')
    personal_pension = _amount(record.pension_personal)
    personal_housing, company_housing, _ht = _resolved_housing_fund_values(record)
    company_pension = _amount(record.pension_company) + _amount(record.supplementary_pension_company)
    company_medical = _resolved_company_medical(record)
    company_unemployment = _amount(record.unemployment_company)
    company_injury = _amount(record.injury_company)
    company_maternity = _amount(record.maternity_amount)
    company_large_medical = _resolved_company_large_medical(record)
    company_disability = Decimal('0')
    personal_social_burden = _resolved_personal_social_burden(
        record, company_medical=company_medical, social_burden_context=social_burden_context or {},
    )
    personal_housing_burden = _resolved_personal_housing_burden(
        record, company_housing=company_housing, housing_burden_context=housing_burden_context or {},
    )

    # Derived totals
    personal_social_due = personal_medical + personal_unemployment + personal_large_medical + personal_disability + personal_pension
    company_social_total = company_pension + company_medical + company_unemployment + company_injury + company_maternity + company_large_medical + company_disability
    personal_total_with_company = personal_social_due + personal_social_burden + personal_housing
    social_grand_total = personal_social_due + personal_social_burden + company_social_total
    housing_grand_total = personal_housing + company_housing
    overall_total = personal_total_with_company + company_social_total + company_housing

    values = [
        record.company_name or '',          # 0: 主体
        _region_label(record.region),        # 1: 区域
        record.person_name or '',            # 2: 员工姓名（辅助）
        record.id_number or '',              # 3: 身份证
        record.employee_id or '',            # 4: 工号
        None,                                # 5: separator
        record.person_name or '',            # 6: 员工姓名
        record.employee_id or '',            # 7: 工号
        personal_medical,                    # 8: 个人医疗保险
        personal_unemployment,               # 9: 个人失业保险
        personal_large_medical,              # 10: 个人大病医疗
        personal_disability,                 # 11: 个人残疾保障金
        personal_pension,                    # 12: 个人养老保险
        personal_housing,                    # 13: 个人公积金
        company_pension,                     # 14: 公司养老保险
        company_medical,                     # 15: 公司医疗保险
        company_unemployment,                # 16: 公司失业保险
        company_injury,                      # 17: 公司工伤保险
        company_maternity,                   # 18: 公司生育保险
        company_large_medical,               # 19: 公司大病医疗
        company_disability,                  # 20: 公司残疾保障金
        company_housing,                     # 21: 公司公积金
        personal_social_burden,              # 22: 个人社保承担额
        personal_housing_burden,             # 23: 个人公积金承担额
        None,                                # 24: blank
        None,                                # 25: blank
        personal_social_due,                 # 26: 个人社保应缴纳总额
        personal_social_due,                 # 27: 个人承担检验
        Decimal('0'),                        # 28: 个人社保检验 (difference)
        personal_housing,                    # 29: 个人公积金
        personal_total_with_company,         # 30: 个人+单位合计承担总额
        None,                                # 31: blank
        company_social_total,                # 32: 单位承担社保
        company_social_total,                # 33: 公司承担检验
        Decimal('0'),                        # 34: 检验值
        company_housing,                     # 35: 单位承担公积金
        company_social_total + company_housing,  # 36: 单位社保+公积金合计
        None,                                # 37: blank
        None,                                # 38: blank
        social_grand_total,                  # 39: 社保：个人+单位
        housing_grand_total,                 # 40: 公积金：个人+单位
        overall_total,                       # 41: 个人+单位合计
    ]

    assert len(values) == len(TOOL_HEADERS), (
        f"_tool_row_values produced {len(values)} values but TOOL_HEADERS has {len(TOOL_HEADERS)} entries"
    )
    return values
