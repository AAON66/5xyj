"""Employee portal endpoints (token-bound, employee role only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.core.auth import AuthUser
from backend.app.dependencies import get_db, require_role
from backend.app.services.employee_service import (
    EmployeeSelfServiceNotFoundError,
    lookup_employee_portal,
)

router = APIRouter(prefix='/employees', tags=['employee-portal'])


@router.get('/self-service/my-records')
def employee_portal_records_endpoint(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("employee")),
):
    try:
        result = lookup_employee_portal(db, employee_id=user.username)
    except EmployeeSelfServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response(result.model_dump(mode='json'), message='Employee portal records retrieved.')
