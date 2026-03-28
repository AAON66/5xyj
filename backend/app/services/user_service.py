from __future__ import annotations

import logging
from typing import Optional

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlalchemy.orm import Session

from backend.app.core.auth import InvalidCredentialsError
from backend.app.models.user import User

logger = logging.getLogger(__name__)

_password_hash = PasswordHash((BcryptHasher(),))


class UsernameExistsError(ValueError):
    """Raised when attempting to create/update a user with a taken username."""


def hash_password(plain: str) -> str:
    return _password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _password_hash.verify(plain, hashed)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def authenticate_user_login(db: Session, username: str, password: str) -> User:
    """Authenticate an admin/HR user by username and password.

    Raises InvalidCredentialsError if the user is not found, password is wrong,
    or the account is disabled.
    """
    user = get_user_by_username(db, username.strip())
    if user is None:
        raise InvalidCredentialsError("Invalid username or password.")
    if not user.is_active:
        raise InvalidCredentialsError("Invalid username or password.")
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError("Invalid username or password.")
    return user


def create_user(
    db: Session,
    username: str,
    password: str,
    role: str,
    display_name: str = "",
) -> User:
    """Create a new user account. Raises UsernameExistsError if username taken."""
    existing = get_user_by_username(db, username.strip())
    if existing is not None:
        raise UsernameExistsError(f"Username '{username}' already exists.")

    user = User(
        username=username.strip(),
        hashed_password=hash_password(password),
        role=role,
        display_name=display_name,
        is_active=True,
        must_change_password=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: str, **kwargs) -> Optional[User]:
    """Update user fields. Returns None if user not found.
    Raises UsernameExistsError if new username is taken."""
    user = get_user_by_id(db, user_id)
    if user is None:
        return None

    if "username" in kwargs and kwargs["username"] is not None:
        new_username = kwargs["username"].strip()
        if new_username != user.username:
            existing = get_user_by_username(db, new_username)
            if existing is not None:
                raise UsernameExistsError(f"Username '{new_username}' already exists.")
            user.username = new_username

    for field in ("role", "display_name", "is_active"):
        if field in kwargs and kwargs[field] is not None:
            setattr(user, field, kwargs[field])

    db.commit()
    db.refresh(user)
    return user


def reset_user_password(db: Session, user_id: str, new_password: str) -> Optional[User]:
    """Reset a user's password. Returns None if user not found."""
    user = get_user_by_id(db, user_id)
    if user is None:
        return None

    user.hashed_password = hash_password(new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    """Return all users ordered by created_at."""
    return db.query(User).order_by(User.created_at).all()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get user by UUID string."""
    return db.query(User).filter(User.id == user_id).first()


def seed_default_admin(db: Session) -> None:
    """Create a default admin user if none exists.  Idempotent."""
    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin is not None:
        logger.info("Default admin already exists, skipping seed.")
        return

    admin = User(
        username="admin",
        hashed_password=hash_password("admin"),
        role="admin",
        display_name="Default Admin",
        must_change_password=True,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    logger.info("Default admin user seeded (username=admin, must_change_password=True).")
