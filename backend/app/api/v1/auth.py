from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.core.auth import InvalidCredentialsError, issue_access_token, role_display_name
from backend.app.dependencies import get_db, require_authenticated_user
from backend.app.models.employee_master import EmployeeMaster
from backend.app.schemas.auth import (
    AuthLoginRequest,
    AuthLoginResponse,
    AuthUserRead,
    EmployeeVerifyRequest,
    EmployeeVerifyResponse,
)
from backend.app.services.rate_limiter import RateLimiter
from backend.app.services.user_service import authenticate_user_login

router = APIRouter(prefix='/auth', tags=['auth'])

_employee_rate_limiter = RateLimiter(max_failures=5, lockout_seconds=900)


@router.post('/login')
def login_endpoint(request: Request, payload: AuthLoginRequest = Body(...), db: Session = Depends(get_db)):
    try:
        user = authenticate_user_login(db, username=payload.username, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    settings = request.app.state.settings
    access_token, expires_at = issue_access_token(
        settings.auth_secret_key,
        sub=user.username,
        role=user.role,
        expire_minutes=settings.auth_token_expire_minutes,
    )
    response = AuthLoginResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=AuthUserRead(
            username=user.username,
            role=user.role,
            display_name=user.display_name or role_display_name(user.role),
            must_change_password=user.must_change_password,
        ),
    )
    return success_response(response.model_dump(mode='json'), message='Login succeeded.')


@router.post('/employee-verify')
def employee_verify_endpoint(
    request: Request,
    payload: EmployeeVerifyRequest = Body(...),
    db: Session = Depends(get_db),
):
    # Check rate limit
    if _employee_rate_limiter.is_locked(payload.employee_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please try again later.",
        )

    # Query employee master
    employee = (
        db.query(EmployeeMaster)
        .filter(
            EmployeeMaster.employee_id == payload.employee_id,
            EmployeeMaster.id_number == payload.id_number,
            EmployeeMaster.person_name == payload.person_name,
            EmployeeMaster.active == True,  # noqa: E712
        )
        .first()
    )

    if employee is None:
        _employee_rate_limiter.record_failure(payload.employee_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification failed.",
        )

    # Success -- reset rate limiter and issue token
    _employee_rate_limiter.reset(payload.employee_id)
    settings = request.app.state.settings
    access_token, expires_at = issue_access_token(
        settings.auth_secret_key,
        sub=payload.employee_id,
        role="employee",
        expire_minutes=settings.employee_token_expire_minutes,
    )
    response = EmployeeVerifyResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=AuthUserRead(
            username=payload.employee_id,
            role="employee",
            display_name=employee.person_name,
        ),
    )
    return success_response(response.model_dump(mode='json'), message='Employee verification succeeded.')


@router.get('/me')
def get_current_user_endpoint(user=Depends(require_authenticated_user)):
    payload = AuthUserRead(username=user.username, role=user.role, display_name=role_display_name(user.role))
    return success_response(payload.model_dump(mode='json'), message='Authenticated user retrieved.')
