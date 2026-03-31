from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import error_response, success_response
from backend.app.core.auth import AuthUser
from backend.app.dependencies import get_db, require_authenticated_user
from backend.app.schemas.api_key import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyListResponse,
    ApiKeyRead,
)
from backend.app.services.api_key_service import (
    ApiKeyLimitExceededError,
    create_api_key,
    get_api_key,
    list_api_keys,
    revoke_api_key,
)
from backend.app.services.audit_service import log_audit
from backend.app.services.user_service import get_user_by_id
from backend.app.utils.request_helpers import get_client_ip

router = APIRouter(prefix="/api-keys", tags=["API Key 管理"])


@router.post("/", status_code=201)
def create_api_key_endpoint(
    request: Request,
    body: ApiKeyCreateRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(require_authenticated_user),
):
    """Create a new API key bound to a specific user. Returns raw key once."""
    # Look up target user to get username and role
    target_user = get_user_by_id(db, body.owner_id)
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found.",
        )

    try:
        record, raw_key = create_api_key(
            db,
            name=body.name,
            owner_id=target_user.id,
            owner_username=target_user.username,
            owner_role=target_user.role,
        )
    except ApiKeyLimitExceededError:
        return error_response(
            code="AUTH_004",
            message="每个用户最多创建 5 个 API Key",
            status_code=400,
        )

    log_audit(
        db,
        action="api_key_create",
        actor_username=current_user.username,
        actor_role=current_user.role,
        ip_address=get_client_ip(request),
        resource_type="api_key",
        resource_id=record.id,
        detail={"key_name": body.name, "owner_username": target_user.username},
        success=True,
    )

    response = ApiKeyCreateResponse(
        id=record.id,
        name=record.name,
        key=raw_key,
        key_prefix=record.key_prefix,
        owner_username=record.owner_username,
        owner_role=record.owner_role,
        created_at=record.created_at,
    )
    return success_response(response.model_dump(mode="json"), status_code=201)


@router.get("/")
def list_api_keys_endpoint(
    db: Session = Depends(get_db),
    owner_id: Optional[str] = Query(None, description="Filter by owner user ID"),
):
    """List all API keys, optionally filtered by owner_id."""
    keys = list_api_keys(db, owner_id=owner_id)
    items = [ApiKeyRead.model_validate(k) for k in keys]
    response = ApiKeyListResponse(items=items, total=len(items))
    return success_response(response.model_dump(mode="json"))


@router.get("/{key_id}")
def get_api_key_endpoint(
    key_id: str,
    db: Session = Depends(get_db),
):
    """Get a single API key by ID."""
    record = get_api_key(db, key_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found.",
        )
    return success_response(ApiKeyRead.model_validate(record).model_dump(mode="json"))


@router.delete("/{key_id}")
def revoke_api_key_endpoint(
    key_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(require_authenticated_user),
):
    """Revoke an API key."""
    record = revoke_api_key(db, key_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found.",
        )

    log_audit(
        db,
        action="api_key_revoke",
        actor_username=current_user.username,
        actor_role=current_user.role,
        ip_address=get_client_ip(request),
        resource_type="api_key",
        resource_id=record.id,
        detail={"key_name": record.name, "owner_username": record.owner_username},
        success=True,
    )
    return success_response({"message": "API Key has been revoked."})
