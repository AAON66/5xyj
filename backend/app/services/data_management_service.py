"""Service layer for data management: filtering, pagination, summaries."""

from __future__ import annotations

from backend.app.models.enums import MatchStatus
from backend.app.models.match_result import MatchResult
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
from backend.app.utils.period_utils import coalesce_billing_period
from sqlalchemy import or_
from sqlalchemy.orm import Session


def _to_float(val: object) -> float:
    """Convert a value (Decimal, int, None) to float safely."""
    if val is None:
        return 0.0
    return float(val)


def _query_records(
    db: Session,
    *,
    regions: list[str] | None = None,
    company_names: list[str] | None = None,
    match_filter: str | None = None,
) -> list[NormalizedRecord]:
    query = db.query(NormalizedRecord)

    if regions:
        query = query.filter(NormalizedRecord.region.in_(regions))
    if company_names:
        query = query.filter(NormalizedRecord.company_name.in_(company_names))

    if match_filter == 'matched':
        query = query.join(MatchResult, MatchResult.normalized_record_id == NormalizedRecord.id)
        query = query.filter(MatchResult.match_status == MatchStatus.MATCHED)
    elif match_filter == 'unmatched':
        query = query.outerjoin(MatchResult, MatchResult.normalized_record_id == NormalizedRecord.id)
        query = query.filter(
            or_(MatchResult.id.is_(None), MatchResult.match_status != MatchStatus.MATCHED)
        )

    ordered_records = query.order_by(NormalizedRecord.created_at.desc(), NormalizedRecord.id.asc()).all()
    deduped: list[NormalizedRecord] = []
    seen_ids: set[str] = set()
    for record in ordered_records:
        if record.id in seen_ids:
            continue
        seen_ids.add(record.id)
        deduped.append(record)
    return deduped


def _effective_billing_period(record: NormalizedRecord) -> str | None:
    raw_payload = record.raw_payload if isinstance(record.raw_payload, dict) else {}
    merged_sources = raw_payload.get("merged_sources")
    merged_candidates: list[object] = []
    if isinstance(merged_sources, list):
        for source in merged_sources:
            if not isinstance(source, dict):
                continue
            merged_candidates.append(source.get("source_file_name"))
            merged_candidates.append(source.get("raw_header_signature"))

    return coalesce_billing_period(
        record.billing_period,
        record.period_start,
        record.period_end,
        record.source_file_name,
        record.raw_header_signature,
        *merged_candidates,
    )


def _normalize_period_filters(billing_periods: list[str] | None) -> set[str] | None:
    if not billing_periods:
        return None

    normalized = {
        period
        for value in billing_periods
        if (period := coalesce_billing_period(value)) is not None
    }
    return normalized or None


def _matches_period_filter(record: NormalizedRecord, billing_periods: set[str] | None) -> bool:
    if billing_periods is None:
        return True
    return _effective_billing_period(record) in billing_periods


def _build_record_read(record: NormalizedRecord) -> NormalizedRecordRead:
    return NormalizedRecordRead(
        id=record.id,
        batch_id=record.batch_id,
        person_name=record.person_name,
        id_number=record.id_number,
        employee_id=record.employee_id,
        company_name=record.company_name,
        region=record.region,
        billing_period=_effective_billing_period(record),
        payment_base=_to_float(record.payment_base) if record.payment_base is not None else None,
        total_amount=_to_float(record.total_amount) if record.total_amount is not None else None,
        company_total_amount=_to_float(record.company_total_amount) if record.company_total_amount is not None else None,
        personal_total_amount=_to_float(record.personal_total_amount) if record.personal_total_amount is not None else None,
        pension_company=_to_float(record.pension_company) if record.pension_company is not None else None,
        pension_personal=_to_float(record.pension_personal) if record.pension_personal is not None else None,
        medical_company=_to_float(record.medical_company) if record.medical_company is not None else None,
        medical_personal=_to_float(record.medical_personal) if record.medical_personal is not None else None,
        medical_maternity_company=_to_float(record.medical_maternity_company)
        if record.medical_maternity_company is not None
        else None,
        unemployment_company=_to_float(record.unemployment_company)
        if record.unemployment_company is not None
        else None,
        unemployment_personal=_to_float(record.unemployment_personal)
        if record.unemployment_personal is not None
        else None,
        injury_company=_to_float(record.injury_company) if record.injury_company is not None else None,
        supplementary_medical_company=_to_float(record.supplementary_medical_company)
        if record.supplementary_medical_company is not None
        else None,
        supplementary_pension_company=_to_float(record.supplementary_pension_company)
        if record.supplementary_pension_company is not None
        else None,
        large_medical_personal=_to_float(record.large_medical_personal)
        if record.large_medical_personal is not None
        else None,
        housing_fund_personal=_to_float(record.housing_fund_personal)
        if record.housing_fund_personal is not None
        else None,
        housing_fund_company=_to_float(record.housing_fund_company)
        if record.housing_fund_company is not None
        else None,
        housing_fund_total=_to_float(record.housing_fund_total) if record.housing_fund_total is not None else None,
        created_at=record.created_at,
    )


def list_normalized_records(
    db: Session,
    *,
    regions: list[str] | None = None,
    company_names: list[str] | None = None,
    billing_periods: list[str] | None = None,
    match_filter: str | None = None,
    page: int = 0,
    page_size: int = 20,
) -> PaginatedRecordsRead:
    """List normalized records with optional filters and deterministic pagination."""
    normalized_periods = _normalize_period_filters(billing_periods)
    records = [
        record
        for record in _query_records(
            db,
            regions=regions,
            company_names=company_names,
            match_filter=match_filter,
        )
        if _matches_period_filter(record, normalized_periods)
    ]

    total = len(records)
    page_records = records[page * page_size:(page + 1) * page_size]
    items = [_build_record_read(record) for record in page_records]
    return PaginatedRecordsRead(items=items, total=total, page=page, page_size=page_size)


def get_filter_options(
    db: Session,
    *,
    regions: list[str] | None = None,
    company_names: list[str] | None = None,
) -> FilterOptionsRead:
    """Get cascading filter options."""
    region_rows = (
        db.query(NormalizedRecord.region)
        .filter(NormalizedRecord.region.isnot(None))
        .distinct()
        .order_by(NormalizedRecord.region.asc())
        .all()
    )
    all_regions = [row[0] for row in region_rows]

    company_query = db.query(NormalizedRecord.company_name).filter(
        NormalizedRecord.company_name.isnot(None)
    )
    if regions:
        company_query = company_query.filter(NormalizedRecord.region.in_(regions))
    company_rows = company_query.distinct().order_by(NormalizedRecord.company_name.asc()).all()
    companies = [row[0] for row in company_rows]

    scoped_records = _query_records(db, regions=regions, company_names=company_names)
    periods = sorted(
        {
            period
            for record in scoped_records
            if (period := _effective_billing_period(record)) is not None
        },
        reverse=True,
    )

    return FilterOptionsRead(regions=all_regions, companies=companies, periods=periods)


def get_employee_summary(
    db: Session,
    *,
    regions: list[str] | None = None,
    company_names: list[str] | None = None,
    billing_periods: list[str] | None = None,
    page: int = 0,
    page_size: int = 20,
) -> PaginatedEmployeeSummaryRead:
    """Employee-level summary grouped by employee_id/person_name/company_name/region."""
    normalized_periods = _normalize_period_filters(billing_periods)
    grouped: dict[tuple[str | None, str | None, str | None, str | None], dict[str, object]] = {}

    for record in _query_records(db, regions=regions, company_names=company_names):
        effective_period = _effective_billing_period(record)
        if normalized_periods is not None and effective_period not in normalized_periods:
            continue

        key = (record.employee_id, record.person_name, record.company_name, record.region)
        aggregate = grouped.setdefault(
            key,
            {
                "employee_id": record.employee_id,
                "person_name": record.person_name,
                "company_name": record.company_name,
                "region": record.region,
                "latest_period": None,
                "company_total": 0.0,
                "personal_total": 0.0,
                "total": 0.0,
            },
        )

        if effective_period and (
            aggregate["latest_period"] is None or effective_period > aggregate["latest_period"]
        ):
            aggregate["latest_period"] = effective_period
        aggregate["company_total"] += _to_float(record.company_total_amount)
        aggregate["personal_total"] += _to_float(record.personal_total_amount)
        aggregate["total"] += _to_float(record.total_amount)

    rows = sorted(
        grouped.values(),
        key=lambda item: (
            item["person_name"] is None,
            item["person_name"] or "",
            item["employee_id"] is None,
            item["employee_id"] or "",
        ),
    )
    total = len(rows)
    page_rows = rows[page * page_size:(page + 1) * page_size]

    items = [
        EmployeeSummaryRead(
            employee_id=row["employee_id"],
            person_name=row["person_name"],
            company_name=row["company_name"],
            region=row["region"],
            latest_period=row["latest_period"],
            company_total=row["company_total"],
            personal_total=row["personal_total"],
            total=row["total"],
        )
        for row in page_rows
    ]

    return PaginatedEmployeeSummaryRead(items=items, total=total, page=page, page_size=page_size)


def get_period_summary(
    db: Session,
    *,
    regions: list[str] | None = None,
    company_names: list[str] | None = None,
    page: int = 0,
    page_size: int = 20,
) -> PaginatedPeriodSummaryRead:
    """Period-level summary grouped by effective billing_period."""
    grouped: dict[str, dict[str, float | int | str]] = {}

    for record in _query_records(db, regions=regions, company_names=company_names):
        effective_period = _effective_billing_period(record)
        if effective_period is None:
            continue

        aggregate = grouped.setdefault(
            effective_period,
            {
                "billing_period": effective_period,
                "total_count": 0,
                "company_total": 0.0,
                "personal_total": 0.0,
                "total": 0.0,
            },
        )
        aggregate["total_count"] += 1
        aggregate["company_total"] += _to_float(record.company_total_amount)
        aggregate["personal_total"] += _to_float(record.personal_total_amount)
        aggregate["total"] += _to_float(record.total_amount)

    rows = []
    for billing_period in sorted(grouped.keys(), reverse=True):
        row = grouped[billing_period]
        total_count = int(row["total_count"])
        company_total = float(row["company_total"])
        personal_total = float(row["personal_total"])
        rows.append(
            PeriodSummaryRead(
                billing_period=billing_period,
                total_count=total_count,
                company_total=company_total,
                personal_total=personal_total,
                total=float(row["total"]),
                avg_personal=personal_total / total_count if total_count else 0.0,
                avg_company=company_total / total_count if total_count else 0.0,
            )
        )

    total = len(rows)
    items = rows[page * page_size:(page + 1) * page_size]
    return PaginatedPeriodSummaryRead(items=items, total=total, page=page, page_size=page_size)
