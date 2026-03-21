from __future__ import annotations

from dataclasses import dataclass


CANONICAL_FIELDS = {
    "person_name",
    "id_type",
    "id_number",
    "employee_id",
    "social_security_number",
    "company_name",
    "region",
    "billing_period",
    "period_start",
    "period_end",
    "payment_base",
    "payment_salary",
    "housing_fund_account",
    "housing_fund_base",
    "housing_fund_personal",
    "housing_fund_company",
    "housing_fund_total",
    "total_amount",
    "company_total_amount",
    "personal_total_amount",
    "pension_company",
    "pension_personal",
    "medical_company",
    "medical_personal",
    "medical_maternity_company",
    "maternity_amount",
    "unemployment_company",
    "unemployment_personal",
    "injury_company",
    "supplementary_medical_company",
    "supplementary_pension_company",
    "large_medical_personal",
    "late_fee",
    "interest",
}


NORMALIZATION_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("（", "("),
    ("）", ")"),
    ("【", "("),
    ("】", ")"),
    ("：", ":"),
    ("／", "/"),
    ("社會", "社会"),
    ("职工基本医疗保险费", "职工基本医疗保险"),
    ("城镇企业职工基本养老保险费", "城镇企业职工基本养老保险"),
    ("失业保险费", "失业保险"),
    ("工伤保险费", "工伤保险"),
)


def normalize_signature(signature: str) -> str:
    normalized = signature.strip().lower().replace(" ", "")
    for source, target in NORMALIZATION_REPLACEMENTS:
        normalized = normalized.replace(source.lower(), target.lower())
    return normalized


@dataclass(frozen=True, slots=True)
class AliasRule:
    canonical_field: str
    patterns: tuple[str, ...]
    confidence: float = 0.98
    regions: tuple[str, ...] = ()
    excludes: tuple[str, ...] = ()

    def matches(self, signature: str, region: str | None = None) -> bool:
        normalized_signature = normalize_signature(signature)
        normalized_patterns = tuple(normalize_signature(pattern) for pattern in self.patterns)
        normalized_excludes = tuple(normalize_signature(pattern) for pattern in self.excludes)
        if self.regions and (region or "") not in self.regions:
            return False
        if any(pattern not in normalized_signature for pattern in normalized_patterns):
            return False
        if any(exclude in normalized_signature for exclude in normalized_excludes):
            return False
        return True


MANUAL_ALIAS_RULES: tuple[AliasRule, ...] = (
    AliasRule("person_name", ("姓名",), confidence=0.99),
    AliasRule("id_number", ("证件号码",), confidence=0.99),
    AliasRule("id_type", ("证件类型",), confidence=0.99),
    AliasRule("social_security_number", ("个人社保号",), confidence=0.99),
    AliasRule("period_start", ("费款所属期起",), confidence=0.99),
    AliasRule("period_end", ("费款所属期止",), confidence=0.99),
    AliasRule("billing_period", ("费款所属期",), excludes=("起", "止"), confidence=0.98),
    AliasRule("billing_period", ("建账年月",), confidence=0.98),
    AliasRule("payment_salary", ("缴费工资",), confidence=0.94),
    AliasRule("payment_base", ("缴费基数",), confidence=0.94),
    AliasRule("total_amount", ("应缴金额合计",), confidence=0.98),
    AliasRule("total_amount", ("总金额",), confidence=0.97),
    AliasRule("total_amount", ("应收金额",), confidence=0.97),
    AliasRule("total_amount", ("总计",), confidence=0.95),
    AliasRule("company_total_amount", ("单位部分合计",), confidence=0.98),
    AliasRule("company_total_amount", ("单位缴费总金额",), confidence=0.98),
    AliasRule("company_total_amount", ("单位社保合计",), confidence=0.98),
    AliasRule("personal_total_amount", ("个人部分合计",), confidence=0.98),
    AliasRule("personal_total_amount", ("个人缴费总金额",), confidence=0.98),
    AliasRule("personal_total_amount", ("个人社保合计",), confidence=0.98),
    AliasRule("pension_company", ("基本养老保险(单位缴纳)", "应缴金额"), confidence=0.99),
    AliasRule("pension_personal", ("基本养老保险(个人缴纳)", "应缴金额"), confidence=0.99),
    AliasRule("pension_company", ("基本养老保险(单位)", "应缴费额"), confidence=0.98),
    AliasRule("pension_personal", ("基本养老保险(个人)", "应缴费额"), confidence=0.98),
    AliasRule("pension_company", ("职工基本养老保险(单位缴纳)",), confidence=0.98),
    AliasRule("pension_personal", ("职工基本养老保险(个人缴纳)",), confidence=0.98),
    AliasRule("pension_company", ("基本养老应缴费额", "单位部分"), confidence=0.97),
    AliasRule("pension_personal", ("基本养老应缴费额", "个人部分"), confidence=0.97),
    AliasRule("pension_company", ("单位缴纳", "养老保险应缴费额"), regions=("wuhan",), confidence=0.97),
    AliasRule("pension_personal", ("个人缴纳", "养老保险应缴费额"), regions=("wuhan",), confidence=0.97),
    AliasRule("pension_company", ("城镇企业职工基本养老保险", "单位应缴"), regions=("xiamen",), confidence=0.97),
    AliasRule("pension_personal", ("城镇企业职工基本养老保险", "个人应缴"), regions=("xiamen",), confidence=0.97),
    AliasRule("unemployment_company", ("失业保险(单位缴纳)", "应缴金额"), confidence=0.99),
    AliasRule("unemployment_personal", ("失业保险(个人缴纳)", "应缴金额"), confidence=0.99),
    AliasRule("unemployment_company", ("失业保险(单位)", "应缴费额"), confidence=0.98),
    AliasRule("unemployment_personal", ("失业保险(个人)", "应缴费额"), confidence=0.98),
    AliasRule("unemployment_company", ("失业保险", "单位应缴"), confidence=0.97),
    AliasRule("unemployment_personal", ("失业保险", "个人应缴"), confidence=0.97),
    AliasRule("unemployment_company", ("失业应缴费额", "单位部分"), confidence=0.97),
    AliasRule("unemployment_personal", ("失业应缴费额", "个人部分"), confidence=0.97),
    AliasRule("unemployment_company", ("单位缴纳", "失业保险应缴费额"), regions=("wuhan",), confidence=0.97),
    AliasRule("unemployment_personal", ("个人缴纳", "失业保险应缴费额"), regions=("wuhan",), confidence=0.97),
    AliasRule("unemployment_company", ("失业保险(单位缴纳)",), regions=("changsha",), confidence=0.94),
    AliasRule("unemployment_personal", ("失业保险(个人缴纳)",), regions=("changsha",), confidence=0.94),
    AliasRule("pension_company", ("职工基本养老保险(单位缴纳)",), regions=("changsha",), confidence=0.94),
    AliasRule("pension_personal", ("职工基本养老保险(个人缴纳)",), regions=("changsha",), confidence=0.94),
    AliasRule("medical_company", ("职工基本医疗保险(单位缴纳)",), regions=("changsha",), confidence=0.94),
    AliasRule("medical_personal", ("职工基本医疗保险(个人缴纳)",), regions=("changsha",), confidence=0.94),
    AliasRule("medical_maternity_company", ("基本医疗保险(含生育)(单位缴纳)", "应缴金额"), confidence=0.99),
    AliasRule("medical_personal", ("基本医疗保险(含生育)(个人缴纳)", "应缴金额"), confidence=0.99),
    AliasRule("medical_company", ("基本医疗保险(单位)", "应缴费额"), confidence=0.98),
    AliasRule("medical_personal", ("基本医疗保险(个人)", "应缴费额"), confidence=0.98),
    AliasRule("medical_company", ("职工基本医疗保险(单位缴纳)",), confidence=0.98),
    AliasRule("medical_personal", ("职工基本医疗保险(个人缴纳)",), confidence=0.98),
    AliasRule("medical_company", ("职工基本医疗保险", "单位应缴"), confidence=0.97),
    AliasRule("medical_personal", ("职工基本医疗保险", "个人应缴"), confidence=0.97),
    AliasRule("medical_company", ("基本医疗应缴费额", "单位部分"), confidence=0.97),
    AliasRule("medical_personal", ("基本医疗应缴费额", "个人部分"), confidence=0.97),
    AliasRule("medical_company", ("单位缴纳", "企业职工基本医疗应缴费额"), regions=("wuhan",), confidence=0.97),
    AliasRule("medical_personal", ("个人缴纳", "企业职工基本医疗应缴费额"), regions=("wuhan",), confidence=0.97),
    AliasRule("injury_company", ("工伤保险", "应缴金额"), confidence=0.98),
    AliasRule("injury_company", ("工伤保险", "应缴费额"), confidence=0.98),
    AliasRule("injury_company", ("工伤保险", "单位应缴"), confidence=0.97),
    AliasRule("injury_company", ("工伤应缴费额",), confidence=0.97),
    AliasRule("injury_company", ("工伤保险",), regions=("changsha",), confidence=0.94),
    AliasRule("injury_company", ("单位缴纳", "工伤保险应缴费额"), regions=("wuhan",), confidence=0.97),
    AliasRule("supplementary_medical_company", ("地方补充医疗(单位)", "应缴费额"), confidence=0.98),
    AliasRule("supplementary_pension_company", ("地方补充养老(单位)", "应缴费额"), confidence=0.98),
    AliasRule("large_medical_personal", ("职工大额医疗互助保险(个人缴纳)",), confidence=0.98),
    AliasRule("late_fee", ("滞纳金",), confidence=0.98),
    AliasRule("interest", ("利息",), confidence=0.98),
)