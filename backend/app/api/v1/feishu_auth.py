"""Feishu OAuth authentication endpoints with CSRF state validation."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import error_response, success_response
from backend.app.core.auth import AuthUser
from backend.app.core.config import Settings
from backend.app.dependencies import get_db, require_authenticated_user
from backend.app.models.user import User
from backend.app.services.feishu_oauth_service import (
    FeishuOAuthError,
    _fetch_feishu_user_info,
    exchange_code_for_user,
    confirm_bind,
)
from backend.app.services.system_setting_service import get_effective_feishu_settings
from backend.app.services.user_service import bind_feishu, unbind_feishu

router = APIRouter(prefix="/auth/feishu", tags=["飞书认证"])

OAUTH_STATE_COOKIE = "feishu_oauth_state"
OAUTH_STATE_MAX_AGE = 600  # 10 minutes


class OAuthCallbackBody(BaseModel):
    code: str
    state: str
    state_signed: str = ""


class ConfirmBindBody(BaseModel):
    pending_token: str
    employee_master_id: str


def _sign_state(state: str, secret: str) -> str:
    """Create HMAC-signed state value: {state}.{signature}"""
    sig = hmac.new(secret.encode(), state.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{state}.{sig}"


def _verify_state(signed_state: str, secret: str) -> str | None:
    """Verify HMAC signature and return original state, or None if invalid."""
    parts = signed_state.rsplit(".", 1)
    if len(parts) != 2:
        return None
    state, sig = parts
    expected_sig = hmac.new(secret.encode(), state.encode(), hashlib.sha256).hexdigest()[:16]
    if not hmac.compare_digest(sig, expected_sig):
        return None
    return state


def _get_settings(request: Request) -> Settings:
    return request.app.state.settings


@router.get("/authorize-url", summary="获取飞书授权 URL", description="生成飞书 OAuth 授权链接，返回 state 签名供前端存储。")
async def get_authorize_url(
    request: Request,
    db: Session = Depends(get_db),
):
    settings = _get_settings(request)
    effective_settings = get_effective_feishu_settings(db, settings)
    if not effective_settings.feishu_oauth_enabled:
        return error_response("FEATURE_DISABLED", "飞书登录功能未启用", 404)

    state = secrets.token_urlsafe(32)
    signed = _sign_state(state, settings.auth_secret_key)

    redirect_uri = settings.feishu_oauth_redirect_uri
    url = (
        f"https://accounts.feishu.cn/open-apis/authen/v1/authorize"
        f"?client_id={effective_settings.feishu_app_id}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )
    return success_response({"url": url, "state_signed": signed})


@router.post("/callback", summary="飞书 OAuth 回调", description="处理飞书 OAuth 回调，验证 state 后交换令牌。返回四种匹配状态。")
async def feishu_oauth_callback(
    body: OAuthCallbackBody,
    request: Request,
    db: Session = Depends(get_db),
):
    settings = _get_settings(request)
    effective_settings = get_effective_feishu_settings(db, settings)
    if not effective_settings.feishu_oauth_enabled:
        return error_response("FEATURE_DISABLED", "飞书登录功能未启用", 404)

    # Validate CSRF state: prefer body.state_signed, fallback to cookie
    signed_value = body.state_signed or request.cookies.get(OAUTH_STATE_COOKIE) or ""
    if not signed_value:
        return error_response("INVALID_STATE", "OAuth state 验证失败，请重新登录", 400)

    original_state = _verify_state(signed_value, settings.auth_secret_key)
    if original_state is None or original_state != body.state:
        return error_response("INVALID_STATE", "OAuth state 验证失败，请重新登录", 400)

    try:
        result = await exchange_code_for_user(
            db,
            body.code,
            settings.model_copy(
                update={
                    "feishu_app_id": effective_settings.feishu_app_id,
                    "feishu_app_secret": effective_settings.feishu_app_secret,
                    "feishu_oauth_enabled": effective_settings.feishu_oauth_enabled,
                }
            ),
        )
    except FeishuOAuthError as e:
        return error_response("OAUTH_ERROR", str(e), 400)

    return success_response(result)


@router.post("/confirm-bind", summary="确认绑定选定员工", description="用临时 token 验证后，将飞书账号绑定到选定的员工。")
async def confirm_bind_endpoint(
    body: ConfirmBindBody,
    request: Request,
    db: Session = Depends(get_db),
):
    settings = _get_settings(request)

    try:
        result = confirm_bind(
            db,
            body.pending_token,
            body.employee_master_id,
            settings,
        )
    except FeishuOAuthError as e:
        error_msg = str(e)
        if error_msg.startswith("CONFLICT:"):
            return error_response("ALREADY_BOUND", error_msg[9:], 409)
        return error_response("BIND_ERROR", error_msg, 400)

    return success_response(result)


@router.get("/bind-authorize-url", summary="获取飞书绑定授权 URL", description="已登录用户获取飞书授权链接，用于绑定飞书账号。")
async def get_bind_authorize_url(
    request: Request,
    current_user: AuthUser = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    settings = _get_settings(request)
    effective_settings = get_effective_feishu_settings(db, settings)

    state_raw = f"bind:{secrets.token_urlsafe(32)}"
    signed = _sign_state(state_raw, settings.auth_secret_key)

    redirect_uri = settings.feishu_oauth_redirect_uri
    url = (
        f"https://accounts.feishu.cn/open-apis/authen/v1/authorize"
        f"?client_id={effective_settings.feishu_app_id}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&state={state_raw}"
    )
    return success_response({"url": url, "state_signed": signed})


@router.post("/bind-callback", summary="飞书绑定回调", description="已登录用户完成飞书授权后，将飞书账号绑定到当前用户。")
async def bind_callback(
    body: OAuthCallbackBody,
    request: Request,
    current_user: AuthUser = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    settings = _get_settings(request)
    effective_settings = get_effective_feishu_settings(db, settings)

    # Validate CSRF state: prefer body.state_signed, fallback to cookie
    signed_value = body.state_signed or request.cookies.get(OAUTH_STATE_COOKIE) or ""
    if not signed_value:
        return error_response("INVALID_STATE", "OAuth state 验证失败", 400)

    original_state = _verify_state(signed_value, settings.auth_secret_key)
    if original_state is None or original_state != body.state:
        return error_response("INVALID_STATE", "OAuth state 验证失败", 400)

    try:
        feishu_info = await _fetch_feishu_user_info(
            body.code,
            settings.model_copy(
                update={
                    "feishu_app_id": effective_settings.feishu_app_id,
                    "feishu_app_secret": effective_settings.feishu_app_secret,
                }
            ),
        )
    except FeishuOAuthError as e:
        return error_response("OAUTH_ERROR", str(e), 400)

    open_id = feishu_info["open_id"]
    union_id = feishu_info["union_id"]
    feishu_name = feishu_info["name"]

    # Check open_id not already bound to another user (T-22-06)
    existing = db.query(User).filter(User.feishu_open_id == open_id).first()
    if existing:
        return error_response("ALREADY_BOUND", "该飞书账号已被其他用户绑定", 409)

    # Find current user in DB and bind
    db_user = db.query(User).filter(User.username == current_user.username).first()
    if not db_user:
        return error_response("USER_NOT_FOUND", "当前用户不存在", 404)

    bind_feishu(db, str(db_user.id), open_id, union_id)

    resp = success_response({"feishu_name": feishu_name, "bound": True})
    resp.delete_cookie(OAUTH_STATE_COOKIE)
    return resp


@router.post("/unbind", summary="解绑飞书账号", description="清空当前用户的飞书绑定信息。")
async def unbind_endpoint(
    request: Request,
    current_user: AuthUser = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.username == current_user.username).first()
    if not db_user:
        return error_response("USER_NOT_FOUND", "当前用户不存在", 404)

    unbind_feishu(db, str(db_user.id))
    return success_response({"unbound": True})
