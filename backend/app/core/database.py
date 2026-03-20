from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import Settings, get_settings


def _sqlite_connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def create_database_engine(settings: Settings | None = None) -> Engine:
    runtime_settings = settings or get_settings()
    engine_kwargs: dict[str, object] = {
        "future": True,
        "pool_pre_ping": True,
        "connect_args": _sqlite_connect_args(runtime_settings.database_url),
    }
    if not runtime_settings.database_url.startswith("sqlite"):
        engine_kwargs["pool_size"] = runtime_settings.database_pool_size
        engine_kwargs["max_overflow"] = runtime_settings.database_max_overflow
    return create_engine(runtime_settings.database_url, **engine_kwargs)


def create_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    engine = create_database_engine(settings)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


engine = create_database_engine()
SessionLocal = create_session_factory()


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()