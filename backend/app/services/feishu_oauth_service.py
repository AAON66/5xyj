"""Feishu OAuth code exchange and user binding service.

Implements 3-level matching:
  1. open_id exact match (already bound user) -> matched
  2. Feishu name unique match EmployeeMaster -> auto_bound
  3. Multiple matches -> pending_candidates
  4. No match -> new_user (create employee role)
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session

from backend.app.core.auth import issue_access_token
from backend.app.core.config import Settings
from backend.app.models.employee_master import EmployeeMaster
from backend.app.models.user import User


class FeishuOAuthError(Exception):
    pass


_FEISHU_TIMEOUT = httpx.Timeout(connect=15.0, read=20.0, write=20.0, pool=20.0)


async def _fetch_feishu_user_info(
    code: str, settings: Settings
) -> dict:
    """Fetch open_id, union_id, name from Feishu OAuth code exchange."""
    try:
        async with httpx.AsyncClient(timeout=_FEISHU_TIMEOUT) as http:
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
    except httpx.TimeoutException as exc:
        raise FeishuOAuthError("连接飞书服务超时，请稍后重试") from exc
    except httpx.HTTPError as exc:
        raise FeishuOAuthError(f"调用飞书接口失败：{exc.__class__.__name__}") from exc

    return {
        "open_id": user_data["open_id"],
        "union_id": user_data.get("union_id", ""),
        "name": user_data.get("name", "Feishu User"),
    }


def _serialize_candidate(emp: EmployeeMaster) -> dict:
    """Serialize EmployeeMaster for pending_candidates response.
    Employee ID is masked: only last 4 chars visible (D-06).
    """
    eid = emp.employee_id or ""
    if len(eid) <= 4:
        masked = "****" + eid
    else:
        masked = "****" + eid[-4:]
    return {
        "employee_master_id": str(emp.id),
        "person_name": emp.person_name,
        "department": emp.department or "",
        "employee_id_masked": masked,
    }


def _find_or_create_user_for_employee(
    db: Session,
    emp: EmployeeMaster,
    open_id: str,
    union_id: str,
    feishu_name: str,
) -> User:
    """Find existing user for employee or create one, then bind feishu_open_id."""
    from backend.app.services.user_service import hash_password

    username = f"emp_{emp.employee_id}"
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        # Create new user inheriting EmployeeMaster data
        user = User(
            username=username,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            role="employee",
            display_name=feishu_name or emp.person_name,
            is_active=True,
            must_change_password=False,
        )
        db.add(user)

    # Bind feishu IDs
    user.feishu_open_id = open_id
    user.feishu_union_id = union_id
    db.commit()
    db.refresh(user)
    return user


def _create_new_feishu_user(
    db: Session,
    open_id: str,
    union_id: str,
    feishu_name: str,
) -> User:
    """Create a brand new user for an unmatched Feishu login."""
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
    return user


def _build_login_response(user: User, settings: Settings, status: str) -> dict:
    """Build response dict with JWT + user info."""
    token, exp = issue_access_token(
        settings.auth_secret_key,
        user.username,
        user.role,
        settings.auth_token_expire_minutes,
    )
    return {
        "status": status,
        "access_token": token,
        "expires_at": exp.isoformat(),
        "role": user.role,
        "username": user.username,
        "display_name": user.display_name,
    }


def _issue_pending_token(
    open_id: str,
    union_id: str,
    feishu_name: str,
    secret_key: str,
    expire_minutes: int = 5,
) -> str:
    """Issue a short-lived JWT for confirm-bind flow (T-22-01)."""
    now = datetime.now(timezone.utc)
    payload = {
        "feishu_open_id": open_id,
        "feishu_union_id": union_id,
        "feishu_name": feishu_name,
        "purpose": "confirm_bind",
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_pending_token(token_str: str, secret_key: str) -> dict:
    """Verify a pending_token JWT and return payload.

    Raises FeishuOAuthError on invalid/expired token.
    """
    try:
        payload = jwt.decode(token_str, secret_key, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise FeishuOAuthError("Pending token has expired")
    except InvalidTokenError:
        raise FeishuOAuthError("Invalid pending token")

    if payload.get("purpose") != "confirm_bind":
        raise FeishuOAuthError("Invalid token purpose")

    return payload


async def exchange_code_for_user(
    db: Session,
    code: str,
    settings: Settings,
) -> dict:
    """
    Exchange Feishu OAuth authorization code for user info,
    then apply 3-level matching logic.

    Returns dict with 'status' field:
      - matched: open_id already bound
      - auto_bound: unique name match, auto-bound
      - pending_candidates: multiple matches, need user selection
      - new_user: no match, created new employee user
    """
    feishu_info = await _fetch_feishu_user_info(code, settings)
    open_id = feishu_info["open_id"]
    union_id = feishu_info["union_id"]
    feishu_name = feishu_info["name"]

    # Layer 1: open_id exact match (already bound user)
    user = db.query(User).filter(User.feishu_open_id == open_id).first()
    if user:
        return _build_login_response(user, settings, "matched")

    # Layer 2 & 3: Match by name in EmployeeMaster
    matches = (
        db.query(EmployeeMaster)
        .filter(EmployeeMaster.person_name == feishu_name, EmployeeMaster.active == True)
        .all()
    )

    if len(matches) == 1:
        # Unique match -> auto-bind
        user = _find_or_create_user_for_employee(db, matches[0], open_id, union_id, feishu_name)
        return _build_login_response(user, settings, "auto_bound")

    if len(matches) > 1:
        # Multiple matches -> return candidates
        pending_token = _issue_pending_token(open_id, union_id, feishu_name, settings.auth_secret_key)
        candidates = [_serialize_candidate(emp) for emp in matches]
        return {
            "status": "pending_candidates",
            "pending_token": pending_token,
            "candidates": candidates,
        }

    # Layer 4: No match -> create new user
    user = _create_new_feishu_user(db, open_id, union_id, feishu_name)
    return _build_login_response(user, settings, "new_user")


def confirm_bind(
    db: Session,
    pending_token: str,
    employee_master_id: str,
    settings: Settings,
) -> dict:
    """Confirm binding after pending_candidates selection (D-05).

    Validates pending_token, checks open_id uniqueness (T-22-06),
    then binds and issues JWT.
    """
    payload = verify_pending_token(pending_token, settings.auth_secret_key)

    open_id = payload["feishu_open_id"]
    union_id = payload.get("feishu_union_id", "")
    feishu_name = payload.get("feishu_name", "")

    # Check open_id not already bound (T-22-06)
    existing = db.query(User).filter(User.feishu_open_id == open_id).first()
    if existing:
        raise FeishuOAuthError("CONFLICT:This Feishu account is already bound to another user")

    # Validate employee_master_id
    emp = db.query(EmployeeMaster).filter(EmployeeMaster.id == employee_master_id).first()
    if not emp:
        raise FeishuOAuthError("Employee master record not found")

    # Bind
    user = _find_or_create_user_for_employee(db, emp, open_id, union_id, feishu_name)
    return _build_login_response(user, settings, "bound")
