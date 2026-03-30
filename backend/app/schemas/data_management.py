from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NormalizedRecordRead(BaseModel):
    id: str
    batch_id: str
    person_name: Optional[str] = None
    id_number: Optional[str] = None
    employee_id: Optional[str] = None
    company_name: Optional[str] = None
    region: Optional[str] = None
    billing_period: Optional[str] = None
    payment_base: Optional[float] = None
    total_amount: Optional[float] = None
    company_total_amount: Optional[float] = None
    personal_total_amount: Optional[float] = None
    pension_company: Optional[float] = None
    pension_personal: Optional[float] = None
    medical_company: Optional[float] = None
    medical_personal: Optional[float] = None
    medical_maternity_company: Optional[float] = None
    unemployment_company: Optional[float] = None
    unemployment_personal: Optional[float] = None
    injury_company: Optional[float] = None
    supplementary_medical_company: Optional[float] = None
    supplementary_pension_company: Optional[float] = None
    large_medical_personal: Optional[float] = None
    housing_fund_personal: Optional[float] = None
    housing_fund_company: Optional[float] = None
    housing_fund_total: Optional[float] = None
    created_at: datetime


class PaginatedRecordsRead(BaseModel):
    items: list[NormalizedRecordRead]
    total: int
    page: int
    page_size: int


class FilterOptionsRead(BaseModel):
    regions: list[str]
    companies: list[str]
    periods: list[str]


class EmployeeSummaryRead(BaseModel):
    employee_id: Optional[str] = None
    person_name: Optional[str] = None
    company_name: Optional[str] = None
    region: Optional[str] = None
    latest_period: Optional[str] = None
    company_total: float
    personal_total: float
    total: float


class PaginatedEmployeeSummaryRead(BaseModel):
    items: list[EmployeeSummaryRead]
    total: int
    page: int
    page_size: int


class PeriodSummaryRead(BaseModel):
    billing_period: str
    total_count: int
    company_total: float
    personal_total: float
    total: float
    avg_personal: float
    avg_company: float


class PaginatedPeriodSummaryRead(BaseModel):
    items: list[PeriodSummaryRead]
    total: int
    page: int
    page_size: int


class BatchQualityRead(BaseModel):
    batch_id: str
    batch_name: str
    record_count: int
    missing_fields: int
    anomalous_amounts: int
    duplicate_records: int


class DataQualityOverviewRead(BaseModel):
    total_missing: int
    total_anomalous: int
    total_duplicates: int
    batches: list[BatchQualityRead]
