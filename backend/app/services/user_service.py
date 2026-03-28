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
