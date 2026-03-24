from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.auth import AuthUser, TokenVerificationError, default_authenticated_user, verify_access_token
from backend.app.core.config import Settings, get_settings as _get_settings
from backend.app.core.database import get_db_session


bearer_scheme = HTTPBearer(auto_error=False)


def get_settings() -> Settings:
    return _get_settings()


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


def require_authenticated_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthUser:
    settings: Settings = request.app.state.settings
    if not settings.auth_enabled:
        return default_authenticated_user()

    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication is required.')

    try:
        return verify_access_token(settings, credentials.credentials)
    except TokenVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
