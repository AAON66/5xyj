from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.api_key import ApiKey


class ApiKeyLimitExceededError(ValueError):
    """Raised when a user already has the maximum number of active API keys."""


class ApiKeyNotFoundError(ValueError):
    """Raised when an API key cannot be found."""


MAX_ACTIVE_KEYS_PER_USER = 5


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key.

    Returns:
        (raw_key, key_prefix, key_hash)
    """
    raw_key = secrets.token_urlsafe(48)
    key_prefix = raw_key[:8]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_prefix, key_hash


def create_api_key(
    db: Session,
    name: str,
    owner_id: str,
    owner_username: str,
    owner_role: str,
) -> tuple[ApiKey, str]:
    """Create a new API key for a user.

    Returns:
        (ApiKey record, raw_key_string)

    Raises:
        ApiKeyLimitExceededError: if user already has MAX_ACTIVE_KEYS_PER_USER active keys.
    """
    active_count = (
        db.query(ApiKey)
        .filter(ApiKey.owner_id == owner_id, ApiKey.is_active == True)  # noqa: E712
        .count()
    )
    if active_count >= MAX_ACTIVE_KEYS_PER_USER:
        raise ApiKeyLimitExceededError(
            f"User already has {MAX_ACTIVE_KEYS_PER_USER} active API keys."
        )

    raw_key, key_prefix, key_hash = generate_api_key()
    record = ApiKey(
        name=name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        owner_id=owner_id,
        owner_username=owner_username,
        owner_role=owner_role,
        is_active=True,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, raw_key


def lookup_api_key(db: Session, raw_key: str) -> Optional[ApiKey]:
    """Look up an API key by its raw value.

    Updates last_used_at if found.
    Returns None if not found or revoked.
    """
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    record = (
        db.query(ApiKey)
        .filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True)  # noqa: E712
        .first()
    )
    if record is not None:
        record.last_used_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
    return record


def revoke_api_key(db: Session, key_id: str) -> Optional[ApiKey]:
    """Revoke an API key by setting is_active=False.

    Returns the updated record, or None if not found.
    """
    record = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if record is None:
        return None
    record.is_active = False
    db.commit()
    db.refresh(record)
    return record


def list_api_keys(db: Session, owner_id: Optional[str] = None) -> list[ApiKey]:
    """List API keys, optionally filtered by owner_id."""
    query = db.query(ApiKey)
    if owner_id is not None:
        query = query.filter(ApiKey.owner_id == owner_id)
    return query.order_by(ApiKey.created_at).all()


def get_api_key(db: Session, key_id: str) -> Optional[ApiKey]:
    """Get a single API key by ID."""
    return db.query(ApiKey).filter(ApiKey.id == key_id).first()
