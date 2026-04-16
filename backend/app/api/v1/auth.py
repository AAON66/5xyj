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
    ChangePasswordRequest,
    EmployeeVerifyRequest,
    EmployeeVerifyResponse,
)
from backend.app.services.audit_service import log_audit
from backend.app.services.rate_limiter import RateLimiter
from backend.app.services.user_service import authenticate_user_login, change_own_password, get_user_by_username
from backend.app.utils.request_helpers import get_client_ip

# Error code prefix: AUTH_xxx
router = APIRouter(prefix='/auth', tags=['\u8ba4\u8bc1'])

_employee_rate_limiter = RateLimiter(max_failures=5, lockout_seconds=900)
_login_rate_limiter = RateLimiter(max_failures=5, lockout_seconds=900)


@router.post('/login', summary="\u7528\u6237\u767b\u5f55", description="\u901a\u8fc7\u7528\u6237\u540d\u548c\u5bc6\u7801\u767b\u5f55\uff0c\u8fd4\u56de JWT \u8bbf\u95ee\u4ee4\u724c\u3002\u652f\u6301\u9891\u7387\u9650\u5236\uff0c5 \u6b21\u5931\u8d25\u540e\u9501\u5b9a 15 \u5206\u949f\u3002")
def login_endpoint(request: Request, payload: AuthLoginRequest = Body(...), db: Session = Depends(get_db)):
    # Check login rate limit (key=username, per D-04)
    rate_key = f"login:{payload.username}"
    if _login_rate_limiter.is_locked(rate_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again in 15 minutes.",
        )

    try:
        user = authenticate_user_login(db, username=payload.username, password=payload.password)
    except InvalidCredentialsError as exc:
        _login_rate_limiter.record_failure(rate_key)
        log_audit(db, action="login_failed", actor_username=payload.username,
                  actor_role="unknown", ip_address=get_client_ip(request),
                  resource_type="session", resource_id=payload.username,
                  detail={"reason": "invalid_credentials"}, success=False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    # Success -- reset rate limiter
    _login_rate_limiter.reset(rate_key)

    settings = request.app.state.settings
    access_token, expires_at = issue_access_token(
        settings.auth_secret_key,
        sub=user.username,
        role=user.role,
        expire_minutes=settings.auth_token_expire_minutes,
    )

    log_audit(db, action="login", actor_username=user.username,
              actor_role=user.role, ip_address=get_client_ip(request),
              resource_type="session", resource_id=user.username,
              detail={"method": "password"}, success=True)

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


@router.post('/employee-verify', summary="\u5458\u5de5\u8eab\u4efd\u9a8c\u8bc1", description="\u901a\u8fc7\u5de5\u53f7\u3001\u8eab\u4efd\u8bc1\u53f7\u548c\u59d3\u540d\u9a8c\u8bc1\u5458\u5de5\u8eab\u4efd\uff0c\u8fd4\u56de\u5458\u5de5\u89d2\u8272\u7684 JWT \u4ee4\u724c\u3002")
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
        log_audit(db, action="employee_verify_failed", actor_username=payload.employee_id,
                  actor_role="unknown", ip_address=get_client_ip(request),
                  resource_type="session", resource_id=payload.employee_id,
                  detail={"reason": "not_found"}, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification failed.",
        )

    # Success -- reset rate limiter and issue token
    _employee_rate_limiter.reset(payload.employee_id)
    log_audit(db, action="employee_verify", actor_username=payload.employee_id,
              actor_role="employee", ip_address=get_client_ip(request),
              resource_type="session", resource_id=payload.employee_id,
              detail={"method": "three_factor"}, success=True)
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


@router.put('/change-password', summary="修改密码", description="用户修改自己的密码，需验证旧密码。仅 admin/hr 角色可用。")
def change_password_endpoint(
    request: Request,
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_authenticated_user),
):
    # Employee uses three-factor auth, no password account
    if current_user.role == 'employee':
        raise HTTPException(status_code=403, detail="Employees do not have password-based accounts.")
    try:
        change_own_password(db, current_user.username, body.old_password, body.new_password)
    except InvalidCredentialsError:
        log_audit(db, action="change_password_failed", actor_username=current_user.username,
                  actor_role=current_user.role, ip_address=get_client_ip(request),
                  resource_type="user", resource_id=current_user.username,
                  detail={"reason": "wrong_old_password"}, success=False)
        raise HTTPException(status_code=400, detail="Old password is incorrect.")
    log_audit(db, action="change_password", actor_username=current_user.username,
              actor_role=current_user.role, ip_address=get_client_ip(request),
              resource_type="user", resource_id=current_user.username,
              detail={}, success=True)
    return success_response({"message": "Password changed successfully."})


@router.get('/me', summary="获取当前用户信息", description="返回当前已认证用户的基本信息，包括用户名、角色、显示名和强制改密状态。")
def get_current_user_endpoint(
    user=Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    # Look up real user record for display_name, must_change_password, feishu_bound
    db_user = get_user_by_username(db, user.username)
    if db_user:
        payload = AuthUserRead(
            username=db_user.username,
            role=db_user.role,
            display_name=db_user.display_name or role_display_name(db_user.role),
            must_change_password=db_user.must_change_password,
            feishu_bound=db_user.feishu_open_id is not None,
        )
        return success_response(payload.model_dump(mode='json'), message='Authenticated user retrieved.')
    # Fallback: no DB record (e.g. auth disabled)
    payload = AuthUserRead(
        username=user.username,
        role=user.role,
        display_name=role_display_name(user.role),
        must_change_password=False,
        feishu_bound=False,
    )
    return success_response(payload.model_dump(mode='json'), message='Authenticated user retrieved.')
