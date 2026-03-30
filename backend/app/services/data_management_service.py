"""Service layer for data management: filtering, pagination, summaries."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.normalized_record import NormalizedRecord
from backend.app.schemas.data_management import (
    EmployeeSummaryRead,
    FilterOptionsRead,
    NormalizedRecordRead,
    PaginatedEmployeeSummaryRead,
    PaginatedPeriodSummaryRead,
    PaginatedRecordsRead,
    PeriodSummaryRead,
)


def _to_float(val: object) -> float:
    """Convert a value (Decimal, int, None) to float safely."""
    if val is None:
        return 0.0
    return float(val)


def list_normalized_records(
    db: Session,
    *,
    region: Optional[str] = None,
    company_name: Optional[str] = None,
    billing_period: Optional[str] = None,
    page: int = 0,
    page_size: int = 20,
) -> PaginatedRecordsRead:
    """List normalized records with optional filters and deterministic pagination."""
    query = db.query(NormalizedRecord)

    if region:
        query = query.filter(NormalizedRecord.region == region)
    if company_name:
        query = query.filter(NormalizedRecord.company_name == company_name)
    if billing_period:
        query = query.filter(NormalizedRecord.billing_period == billing_period)

    total = query.count()

    records = (
        query.order_by(NormalizedRecord.created_at.desc(), NormalizedRecord.id.asc())
        .offset(page * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        NormalizedRecordRead(
            id=r.id,
            batch_id=r.batch_id,
            person_name=r.person_name,
            id_number=r.id_number,
            employee_id=r.employee_id,
            company_name=r.company_name,
            region=r.region,
            billing_period=r.billing_period,
            payment_base=_to_float(r.payment_base) if r.payment_base is not None else None,
            total_amount=_to_float(r.total_amount) if r.total_amount is not None else None,
            company_total_amount=_to_float(r.company_total_amount) if r.company_total_amount is not None else None,
            personal_total_amount=_to_float(r.personal_total_amount) if r.personal_total_amount is not None else None,
            pension_company=_to_float(r.pension_company) if r.pension_company is not None else None,
            pension_personal=_to_float(r.pension_personal) if r.pension_personal is not None else None,
            medical_company=_to_float(r.medical_company) if r.medical_company is not None else None,
            medical_personal=_to_float(r.medical_personal) if r.medical_personal is not None else None,
            medical_maternity_company=_to_float(r.medical_maternity_company) if r.medical_maternity_company is not None else None,
            unemployment_company=_to_float(r.unemployment_company) if r.unemployment_company is not None else None,
            unemployment_personal=_to_float(r.unemployment_personal) if r.unemployment_personal is not None else None,
            injury_company=_to_float(r.injury_company) if r.injury_company is not None else None,
            supplementary_medical_company=_to_float(r.supplementary_medical_company) if r.supplementary_medical_company is not None else None,
            supplementary_pension_company=_to_float(r.supplementary_pension_company) if r.supplementary_pension_company is not None else None,
            large_medical_personal=_to_float(r.large_medical_personal) if r.large_medical_personal is not None else None,
            housing_fund_personal=_to_float(r.housing_fund_personal) if r.housing_fund_personal is not None else None,
            housing_fund_company=_to_float(r.housing_fund_company) if r.housing_fund_company is not None else None,
            housing_fund_total=_to_float(r.housing_fund_total) if r.housing_fund_total is not None else None,
            created_at=r.created_at,
        )
        for r in records
    ]

    return PaginatedRecordsRead(items=items, total=total, page=page, page_size=page_size)


def get_filter_options(
    db: Session,
    *,
    region: Optional[str] = None,
    company_name: Optional[str] = None,
) -> FilterOptionsRead:
    """Get cascading filter options.

    - regions: always all distinct regions (top-level, unscoped)
    - companies: scoped by region if provided
    - periods: scoped by region+company_name if provided
    """
    # Regions: always unscoped
    region_rows = (
        db.query(NormalizedRecord.region)
        .filter(NormalizedRecord.region.isnot(None))
        .distinct()
        .order_by(NormalizedRecord.region.asc())
        .all()
    )
    regions = [r[0] for r in region_rows]

    # Companies: scoped by region
    company_query = db.query(NormalizedRecord.company_name).filter(
        NormalizedRecord.company_name.isnot(None)
    )
    if region:
        company_query = company_query.filter(NormalizedRecord.region == region)
    company_rows = company_query.distinct().order_by(NormalizedRecord.company_name.asc()).all()
    companies = [r[0] for r in company_rows]

    # Periods: scoped by region and company_name
    period_query = db.query(NormalizedRecord.billing_period).filter(
        NormalizedRecord.billing_period.isnot(None)
    )
    if region:
        period_query = period_query.filter(NormalizedRecord.region == region)
    if company_name:
        period_query = period_query.filter(NormalizedRecord.company_name == company_name)
    period_rows = period_query.distinct().order_by(NormalizedRecord.billing_period.desc()).all()
    periods = [r[0] for r in period_rows]

    return FilterOptionsRead(regions=regions, companies=companies, periods=periods)


def get_employee_summary(
    db: Session,
    *,
    region: Optional[str] = None,
    company_name: Optional[str] = None,
    billing_period: Optional[str] = None,
    page: int = 0,
    page_size: int = 20,
) -> PaginatedEmployeeSummaryRead:
    """Employee-level summary grouped by employee_id/person_name/company_name/region."""
    base_query = db.query(
        NormalizedRecord.employee_id,
        NormalizedRecord.person_name,
        NormalizedRecord.company_name,
        NormalizedRecord.region,
        func.max(NormalizedRecord.billing_period).label("latest_period"),
        func.sum(NormalizedRecord.company_total_amount).label("company_total"),
        func.sum(NormalizedRecord.personal_total_amount).label("personal_total"),
        func.sum(NormalizedRecord.total_amount).label("total"),
    )

    if region:
        base_query = base_query.filter(NormalizedRecord.region == region)
    if company_name:
        base_query = base_query.filter(NormalizedRecord.company_name == company_name)
    if billing_period:
        base_query = base_query.filter(NormalizedRecord.billing_period == billing_period)

    grouped = base_query.group_by(
        NormalizedRecord.employee_id,
        NormalizedRecord.person_name,
        NormalizedRecord.company_name,
        NormalizedRecord.region,
    )

    # Total count of groups
    count_subquery = grouped.subquery()
    total = db.query(func.count()).select_from(count_subquery).scalar() or 0

    # Paginated results with deterministic sort
    rows = (
        grouped.order_by(
            NormalizedRecord.person_name.asc().nullslast(),
            NormalizedRecord.employee_id.asc().nullslast(),
        )
        .offset(page * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        EmployeeSummaryRead(
            employee_id=row.employee_id,
            person_name=row.person_name,
            company_name=row.company_name,
            region=row.region,
            latest_period=row.latest_period,
            company_total=_to_float(row.company_total),
            personal_total=_to_float(row.personal_total),
            total=_to_float(row.total),
        )
        for row in rows
    ]

    return PaginatedEmployeeSummaryRead(items=items, total=total, page=page, page_size=page_size)


def get_period_summary(
    db: Session,
    *,
    region: Optional[str] = None,
    company_name: Optional[str] = None,
    page: int = 0,
    page_size: int = 20,
) -> PaginatedPeriodSummaryRead:
    """Period-level summary grouped by billing_period."""
    base_query = db.query(
        NormalizedRecord.billing_period,
        func.count(NormalizedRecord.id).label("total_count"),
        func.sum(NormalizedRecord.company_total_amount).label("company_total"),
        func.sum(NormalizedRecord.personal_total_amount).label("personal_total"),
        func.sum(NormalizedRecord.total_amount).label("total"),
        func.avg(NormalizedRecord.personal_total_amount).label("avg_personal"),
        func.avg(NormalizedRecord.company_total_amount).label("avg_company"),
    ).filter(NormalizedRecord.billing_period.isnot(None))

    if region:
        base_query = base_query.filter(NormalizedRecord.region == region)
    if company_name:
        base_query = base_query.filter(NormalizedRecord.company_name == company_name)

    grouped = base_query.group_by(NormalizedRecord.billing_period)

    # Total count of groups
    count_subquery = grouped.subquery()
    total = db.query(func.count()).select_from(count_subquery).scalar() or 0

    # Paginated results with deterministic sort (newest first)
    rows = (
        grouped.order_by(NormalizedRecord.billing_period.desc())
        .offset(page * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        PeriodSummaryRead(
            billing_period=row.billing_period,
            total_count=row.total_count,
            company_total=_to_float(row.company_total),
            personal_total=_to_float(row.personal_total),
            total=_to_float(row.total),
            avg_personal=_to_float(row.avg_personal),
            avg_company=_to_float(row.avg_company),
        )
        for row in rows
    ]

    return PaginatedPeriodSummaryRead(items=items, total=total, page=page, page_size=page_size)
