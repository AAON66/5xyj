from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from backend.app.api.v1.responses import success_response
from backend.app.core.auth import InvalidCredentialsError, authenticate_login, issue_access_token, role_display_name
from backend.app.dependencies import require_authenticated_user
from backend.app.schemas.auth import AuthLoginRequest, AuthLoginResponse, AuthUserRead

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login')
def login_endpoint(request: Request, payload: AuthLoginRequest = Body(...)):
    try:
        user = authenticate_login(
            request.app.state.settings,
            username=payload.username,
            password=payload.password,
            role=payload.role,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    access_token, expires_at = issue_access_token(request.app.state.settings, user)
    response = AuthLoginResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=AuthUserRead(
            username=user.username,
            role=user.role,
            display_name=role_display_name(user.role),
        ),
    )
    return success_response(response.model_dump(mode='json'), message='Login succeeded.')


@router.get('/me')
def get_current_user_endpoint(user=Depends(require_authenticated_user)):
    payload = AuthUserRead(username=user.username, role=user.role, display_name=role_display_name(user.role))
    return success_response(payload.model_dump(mode='json'), message='Authenticated user retrieved.')
