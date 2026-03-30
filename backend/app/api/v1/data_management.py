"""Data management API endpoints: records, filter options, summaries."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
from backend.app.services.data_management_service import (
    get_employee_summary,
    get_filter_options,
    get_period_summary,
    list_normalized_records,
)

router = APIRouter(prefix='/data-management', tags=['data-management'])


@router.get('/records')
def list_records_endpoint(
    region: Optional[str] = Query(default=None),
    company_name: Optional[str] = Query(default=None),
    billing_period: Optional[str] = Query(default=None),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = list_normalized_records(
        db,
        region=region,
        company_name=company_name,
        billing_period=billing_period,
        page=page,
        page_size=page_size,
    )
    return success_response(result.model_dump(mode='json'))


@router.get('/filter-options')
def filter_options_endpoint(
    region: Optional[str] = Query(default=None),
    company_name: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    result = get_filter_options(db, region=region, company_name=company_name)
    return success_response(result.model_dump(mode='json'))


@router.get('/summary/employees')
def employee_summary_endpoint(
    region: Optional[str] = Query(default=None),
    company_name: Optional[str] = Query(default=None),
    billing_period: Optional[str] = Query(default=None),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = get_employee_summary(
        db,
        region=region,
        company_name=company_name,
        billing_period=billing_period,
        page=page,
        page_size=page_size,
    )
    return success_response(result.model_dump(mode='json'))


@router.get('/summary/periods')
def period_summary_endpoint(
    region: Optional[str] = Query(default=None),
    company_name: Optional[str] = Query(default=None),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = get_period_summary(
        db,
        region=region,
        company_name=company_name,
        page=page,
        page_size=page_size,
    )
    return success_response(result.model_dump(mode='json'))
