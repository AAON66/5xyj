from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


AuthRole = Literal['admin', 'hr', 'employee']


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


def issue_access_token(secret_key: str, sub: str, role: str, expire_minutes: int) -> tuple[str, datetime]:
    """Issue a PyJWT access token with sub, role, iat, exp claims."""
    iat = datetime.now(timezone.utc)
    exp = iat + timedelta(minutes=max(expire_minutes, 1))
    payload = {
        'sub': sub,
        'role': role,
        'iat': iat,
        'exp': exp,
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token, exp


def verify_access_token(secret_key: str, token: str) -> AuthUser:
    """Verify and decode a PyJWT access token, returning an AuthUser."""
    if not token:
        raise TokenVerificationError('Authentication token is required.')
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except ExpiredSignatureError as exc:
        raise TokenVerificationError('Authentication token has expired.') from exc
    except InvalidTokenError as exc:
        raise TokenVerificationError('Authentication token is invalid.') from exc

    username = payload.get('sub')
    role = payload.get('role')

    if not isinstance(username, str) or not username.strip():
        raise TokenVerificationError('Authentication token subject is invalid.')

    return AuthUser(username=username.strip(), role=_normalize_role(role))


def default_authenticated_user() -> AuthUser:
    return AuthUser(username='local-dev', role='admin')


def role_display_name(role: AuthRole) -> str:
    mapping = {
        'admin': '管理员',
        'hr': 'HR',
        'employee': '员工',
    }
    return mapping.get(role, role)


def _normalize_role(value: str) -> AuthRole:
    if value == 'admin':
        return 'admin'
    if value == 'hr':
        return 'hr'
    if value == 'employee':
        return 'employee'
    raise TokenVerificationError('Authentication role is invalid.')
