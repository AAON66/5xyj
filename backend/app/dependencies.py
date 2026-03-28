from __future__ import annotations

from typing import Callable, Optional

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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> AuthUser:
    settings: Settings = request.app.state.settings
    if not settings.auth_enabled:
        return default_authenticated_user()

    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication is required.')

    try:
        return verify_access_token(settings.auth_secret_key, credentials.credentials)
    except TokenVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_role(*allowed_roles: str) -> Callable:
    """Dependency factory that enforces role-based access control.

    Usage::

        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        def admin_endpoint(): ...

        # Or inject the user:
        @router.get("/admin-hr")
        def admin_hr_endpoint(user: AuthUser = Depends(require_role("admin", "hr"))): ...
    """
    def _role_dependency(
        user: AuthUser = Depends(require_authenticated_user),
    ) -> AuthUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return user
    return _role_dependency
