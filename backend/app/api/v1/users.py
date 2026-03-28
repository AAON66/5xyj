from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import error_response, success_response
from backend.app.core.auth import AuthUser
from backend.app.dependencies import get_db, require_authenticated_user
from backend.app.services.audit_service import log_audit
from backend.app.utils.request_helpers import get_client_ip
from backend.app.schemas.users import UserCreate, UserPasswordReset, UserRead, UserUpdate
from backend.app.services.user_service import (
    UsernameExistsError,
    create_user,
    get_user_by_id,
    list_users,
    reset_user_password,
    update_user,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", status_code=201)
def create_user_endpoint(
    request: Request,
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(require_authenticated_user),
):
    try:
        user = create_user(
            db,
            username=body.username,
            password=body.password,
            role=body.role,
            display_name=body.display_name,
        )
    except UsernameExistsError:
        return error_response(
            code="USERNAME_EXISTS",
            message=f"Username '{body.username}' already exists.",
            status_code=409,
        )
    log_audit(db, action="user_create", actor_username=current_user.username,
              actor_role=current_user.role, ip_address=get_client_ip(request),
              resource_type="user", resource_id=user.username,
              detail={"target_username": user.username}, success=True)
    return success_response(UserRead.model_validate(user).model_dump(mode="json"), status_code=201)


@router.get("/")
def list_users_endpoint(db: Session = Depends(get_db)):
    users = list_users(db)
    data = [UserRead.model_validate(u).model_dump(mode="json") for u in users]
    return success_response(data)


@router.get("/{user_id}")
def get_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return success_response(UserRead.model_validate(user).model_dump(mode="json"))


@router.put("/{user_id}")
def update_user_endpoint(
    user_id: str,
    body: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(require_authenticated_user),
):
    kwargs = body.model_dump(exclude_unset=True)
    try:
        user = update_user(db, user_id, **kwargs)
    except UsernameExistsError:
        return error_response(
            code="USERNAME_EXISTS",
            message=f"Username already exists.",
            status_code=409,
        )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    log_audit(db, action="user_update", actor_username=current_user.username,
              actor_role=current_user.role, ip_address=get_client_ip(request),
              resource_type="user", resource_id=user.username,
              detail={"target_username": user.username, "changed_fields": list(kwargs.keys())},
              success=True)
    return success_response(UserRead.model_validate(user).model_dump(mode="json"))


@router.put("/{user_id}/password")
def reset_password_endpoint(
    user_id: str,
    body: UserPasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(require_authenticated_user),
):
    user = reset_user_password(db, user_id, body.new_password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    log_audit(db, action="user_password_reset", actor_username=current_user.username,
              actor_role=current_user.role, ip_address=get_client_ip(request),
              resource_type="user", resource_id=user.username,
              detail={"target_username": user.username}, success=True)
    return success_response({"message": "Password reset successfully."})
