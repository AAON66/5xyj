"""Feishu OAuth code exchange and user binding service."""

from __future__ import annotations

import secrets

import httpx
from sqlalchemy.orm import Session

from backend.app.core.auth import issue_access_token
from backend.app.core.config import Settings
from backend.app.models.user import User


class FeishuOAuthError(Exception):
    pass


async def exchange_code_for_user(
    db: Session,
    code: str,
    settings: Settings,
) -> dict:
    """
    Exchange Feishu OAuth authorization code for user info,
    find or create system user, and issue JWT.

    Returns: {"access_token": str, "expires_at": str, "role": str, "username": str, "display_name": str}
    """
    async with httpx.AsyncClient() as http:
        # 1. Get app_access_token
        app_token_resp = await http.post(
            "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
            json={"app_id": settings.feishu_app_id, "app_secret": settings.feishu_app_secret},
        )
        app_token_resp.raise_for_status()
        app_data = app_token_resp.json()
        if app_data.get("code") != 0:
            raise FeishuOAuthError(f"Failed to get app_access_token: {app_data.get('msg')}")
        app_access_token = app_data["app_access_token"]

        # 2. Exchange code for user_access_token + user info
        user_resp = await http.post(
            "https://open.feishu.cn/open-apis/authen/v1/access_token",
            headers={"Authorization": f"Bearer {app_access_token}"},
            json={"grant_type": "authorization_code", "code": code},
        )
        user_resp.raise_for_status()
        user_data = user_resp.json().get("data", {})
        if not user_data.get("open_id"):
            raise FeishuOAuthError("Failed to get user info from Feishu")

    open_id = user_data["open_id"]
    union_id = user_data.get("union_id", "")
    feishu_name = user_data.get("name", "Feishu User")

    # 3. Find existing user by feishu_open_id
    user = db.query(User).filter(User.feishu_open_id == open_id).first()

    if not user:
        # Create new user with employee role (per D-11)
        from backend.app.services.user_service import hash_password

        username = f"feishu_{open_id[:16]}"
        user = User(
            username=username,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            role="employee",
            display_name=feishu_name,
            is_active=True,
            must_change_password=False,
            feishu_open_id=open_id,
            feishu_union_id=union_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4. Issue system JWT (per D-10)
    token, exp = issue_access_token(
        settings.auth_secret_key,
        user.username,
        user.role,
        settings.auth_token_expire_minutes,
    )
    return {
        "access_token": token,
        "expires_at": exp.isoformat(),
        "role": user.role,
        "username": user.username,
        "display_name": user.display_name,
    }
