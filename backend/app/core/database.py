from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import Settings, get_settings

SQLITE_BUSY_TIMEOUT_MS = 120000


def _sqlite_connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {
            "check_same_thread": False,
            "timeout": SQLITE_BUSY_TIMEOUT_MS / 1000,
        }
    return {}


def _configure_sqlite_engine(engine: Engine) -> None:
    if engine.url.get_backend_name() != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _apply_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


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

    engine = create_engine(runtime_settings.database_url, **engine_kwargs)
    _configure_sqlite_engine(engine)
    return engine


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
