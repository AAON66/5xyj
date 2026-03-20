from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings as _get_settings
from backend.app.core.database import get_db_session


def get_settings() -> Settings:
    return _get_settings()


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()