"""Feishu OAuth authentication endpoints with CSRF state validation."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import error_response, success_response
from backend.app.core.config import Settings
from backend.app.dependencies import get_db
from backend.app.services.feishu_oauth_service import FeishuOAuthError, exchange_code_for_user, confirm_bind
from backend.app.services.system_setting_service import get_effective_feishu_settings

router = APIRouter(prefix="/auth/feishu", tags=["飞书认证"])

OAUTH_STATE_COOKIE = "feishu_oauth_state"
OAUTH_STATE_MAX_AGE = 600  # 10 minutes


class OAuthCallbackBody(BaseModel):
    code: str
    state: str


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


@router.get("/authorize-url", summary="获取飞书授权 URL", description="生成飞书 OAuth 授权链接，并设置 CSRF 状态 Cookie。")
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

    redirect_uri = getattr(settings, "feishu_oauth_redirect_uri", "")
    url = (
        f"https://accounts.feishu.cn/open-apis/authen/v1/authorize"
        f"?client_id={effective_settings.feishu_app_id}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )
    resp = success_response({"url": url})
    resp.set_cookie(
        OAUTH_STATE_COOKIE,
        signed,
        max_age=OAUTH_STATE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,  # secure=True in production
    )
    return resp


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

    # Validate CSRF state via signed cookie (H2)
    cookie_value = request.cookies.get(OAUTH_STATE_COOKIE)
    if not cookie_value:
        return error_response("INVALID_STATE", "OAuth state 验证失败，请重新登录", 400)

    original_state = _verify_state(cookie_value, settings.auth_secret_key)
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

    resp = success_response(result)
    # Delete state cookie after successful validation
    resp.delete_cookie(OAUTH_STATE_COOKIE)
    return resp


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
