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

# Error code prefix: DM_xxx
router = APIRouter(prefix='/data-management', tags=['\u6570\u636e\u7ba1\u7406'])


@router.get('/records', summary="\u67e5\u8be2\u6807\u51c6\u5316\u8bb0\u5f55", description="\u5206\u9875\u67e5\u8be2\u5f52\u4e00\u5316\u540e\u7684\u793e\u4fdd\u8bb0\u5f55\uff0c\u652f\u6301\u6309\u5730\u533a\u3001\u516c\u53f8\u3001\u8d26\u671f\u7b5b\u9009\u3002")
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


@router.get('/filter-options', summary="\u83b7\u53d6\u7b5b\u9009\u9009\u9879", description="\u8fd4\u56de\u53ef\u7528\u7684\u5730\u533a\u3001\u516c\u53f8\u540d\u79f0\u548c\u8d26\u671f\u7b5b\u9009\u9009\u9879\u3002")
def filter_options_endpoint(
    region: Optional[str] = Query(default=None),
    company_name: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    result = get_filter_options(db, region=region, company_name=company_name)
    return success_response(result.model_dump(mode='json'))


@router.get('/summary/employees', summary="\u5458\u5de5\u6c47\u603b", description="\u6309\u5458\u5de5\u7ef4\u5ea6\u6c47\u603b\u793e\u4fdd\u6570\u636e\uff0c\u652f\u6301\u5206\u9875\u548c\u7b5b\u9009\u3002")
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


@router.get('/summary/periods', summary="\u8d26\u671f\u6c47\u603b", description="\u6309\u8d26\u671f\u7ef4\u5ea6\u6c47\u603b\u793e\u4fdd\u6570\u636e\uff0c\u652f\u6301\u5206\u9875\u548c\u7b5b\u9009\u3002")
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
