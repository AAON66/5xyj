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

router = APIRouter(prefix='/employees', tags=['\u5458\u5de5\u95e8\u6237'])


@router.get('/self-service/my-records', summary="\u67e5\u8be2\u6211\u7684\u793e\u4fdd\u8bb0\u5f55", description="\u5458\u5de5\u67e5\u8be2\u81ea\u5df1\u7684\u793e\u4fdd\u516c\u79ef\u91d1\u8bb0\u5f55\u3002\u4ec5\u5458\u5de5\u89d2\u8272\u53ef\u8bbf\u95ee\u3002")
def employee_portal_records_endpoint(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("employee")),
):
    try:
        result = lookup_employee_portal(db, employee_id=user.username)
    except EmployeeSelfServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response(result.model_dump(mode='json'), message='Employee portal records retrieved.')
