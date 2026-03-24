from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from backend.app.core.config import Settings


AuthRole = Literal['admin', 'hr']


@dataclass(frozen=True)
class AuthUser:
    username: str
    role: AuthRole


class AuthError(Exception):
    """Base authentication error."""


class InvalidCredentialsError(AuthError):
    """Raised when a username/password pair is invalid."""


class TokenVerificationError(AuthError):
    """Raised when an access token cannot be trusted."""


def authenticate_login(settings: Settings, username: str, password: str, role: str) -> AuthUser:
    normalized_role = _normalize_role(role)
    expected_username = settings.admin_login_username if normalized_role == 'admin' else settings.hr_login_username
    expected_password = settings.admin_login_password if normalized_role == 'admin' else settings.hr_login_password
    normalized_username = username.strip()

    if not normalized_username or not password:
        raise InvalidCredentialsError('Username and password are required.')

    if not hmac.compare_digest(normalized_username, expected_username) or not hmac.compare_digest(password, expected_password):
        raise InvalidCredentialsError('Invalid username, password, or role.')

    return AuthUser(username=normalized_username, role=normalized_role)


def issue_access_token(settings: Settings, user: AuthUser) -> tuple[str, datetime]:
    issued_at = int(time.time())
    expires_at = datetime.fromtimestamp(
        issued_at + max(settings.auth_token_expire_minutes, 1) * 60,
        tz=timezone.utc,
    )
    payload = {
        'sub': user.username,
        'role': user.role,
        'iat': issued_at,
        'exp': int(expires_at.timestamp()),
    }
    payload_segment = _encode_segment(payload)
    signature_segment = _sign_segment(payload_segment, settings.auth_secret_key)
    return f'{payload_segment}.{signature_segment}', expires_at


def verify_access_token(settings: Settings, token: str) -> AuthUser:
    if not token:
        raise TokenVerificationError('Authentication token is required.')

    try:
        payload_segment, signature_segment = token.split('.', maxsplit=1)
    except ValueError as exc:
        raise TokenVerificationError('Authentication token format is invalid.') from exc

    expected_signature = _sign_segment(payload_segment, settings.auth_secret_key)
    if not hmac.compare_digest(signature_segment, expected_signature):
        raise TokenVerificationError('Authentication token signature is invalid.')

    payload = _decode_segment(payload_segment)
    exp = payload.get('exp')
    username = payload.get('sub')
    role = payload.get('role')

    if not isinstance(exp, int) or exp <= int(time.time()):
        raise TokenVerificationError('Authentication token has expired.')
    if not isinstance(username, str) or not username.strip():
        raise TokenVerificationError('Authentication token subject is invalid.')

    return AuthUser(username=username.strip(), role=_normalize_role(role))


def default_authenticated_user() -> AuthUser:
    return AuthUser(username='local-dev', role='admin')


def role_display_name(role: AuthRole) -> str:
    return '管理员' if role == 'admin' else 'HR'


def _normalize_role(value: str) -> AuthRole:
    if value == 'admin':
        return 'admin'
    if value == 'hr':
        return 'hr'
    raise TokenVerificationError('Authentication role is invalid.')


def _encode_segment(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def _decode_segment(segment: str) -> dict[str, object]:
    try:
        padding = '=' * (-len(segment) % 4)
        decoded = base64.urlsafe_b64decode(segment + padding)
        payload = json.loads(decoded.decode('utf-8'))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TokenVerificationError('Authentication token payload is invalid.') from exc

    if not isinstance(payload, dict):
        raise TokenVerificationError('Authentication token payload is invalid.')
    return payload


def _sign_segment(segment: str, secret_key: str) -> str:
    signature = hmac.new(secret_key.encode('utf-8'), segment.encode('utf-8'), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(signature).decode('ascii').rstrip('=')
