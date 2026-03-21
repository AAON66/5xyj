from __future__ import annotations

import logging
import shutil
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.bootstrap import bootstrap_application, ensure_runtime_directories
from backend.app.core.config import ROOT_DIR, Settings
from backend.app.core.database import create_database_engine, create_session_factory
from backend.app.core.logging import JsonLogFormatter, configure_logging
from backend.app.dependencies import get_settings


ARTIFACTS_DIR = ROOT_DIR / ".test_artifacts" / "runtime_config"


def test_settings_resolve_relative_directories() -> None:
    settings = Settings(
        upload_dir="./custom/uploads",
        samples_dir="./custom/samples",
        templates_dir="./custom/templates",
        outputs_dir="./custom/outputs",
    )

    assert settings.upload_path == (ROOT_DIR / "custom/uploads").resolve()
    assert settings.samples_path == (ROOT_DIR / "custom/samples").resolve()
    assert settings.templates_path == (ROOT_DIR / "custom/templates").resolve()
    assert settings.outputs_path == (ROOT_DIR / "custom/outputs").resolve()


def test_bootstrap_creates_runtime_directories() -> None:
    if ARTIFACTS_DIR.exists():
        shutil.rmtree(ARTIFACTS_DIR)

    settings = Settings(
        upload_dir=str(ARTIFACTS_DIR / "uploads"),
        samples_dir=str(ARTIFACTS_DIR / "samples"),
        templates_dir=str(ARTIFACTS_DIR / "templates"),
        outputs_dir=str(ARTIFACTS_DIR / "outputs"),
        log_format="plain",
    )

    bootstrap_application(settings)

    assert settings.upload_path.exists()
    assert settings.samples_path.exists()
    assert settings.templates_path.exists()
    assert settings.outputs_path.exists()


def test_create_session_factory_supports_sqlite_runtime() -> None:
    database_path = ARTIFACTS_DIR / "runtime.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()

    settings = Settings(database_url=f"sqlite:///{database_path.as_posix()}")
    engine = create_database_engine(settings)
    session_factory = create_session_factory(settings)

    with session_factory() as session:
        result = session.execute(text("SELECT 1")).scalar_one()

    assert result == 1
    assert engine.url.get_backend_name() == "sqlite"


def test_json_log_formatter_outputs_expected_shape() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord("social-security", logging.INFO, __file__, 10, "hello world", args=(), exc_info=None)

    rendered = formatter.format(record)

    assert '"level":"INFO"' in rendered
    assert '"logger":"social-security"' in rendered
    assert '"message":"hello world"' in rendered


def test_dependency_get_settings_returns_settings_instance() -> None:
    settings = get_settings()

    assert isinstance(settings, Settings)


def test_create_database_engine_applies_sqlite_pragmas() -> None:
    database_path = ARTIFACTS_DIR / "runtime-pragmas.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()

    settings = Settings(database_url=f"sqlite:///{database_path.as_posix()}")
    session_factory = create_session_factory(settings)

    with session_factory() as session:
        journal_mode = session.execute(text("PRAGMA journal_mode")).scalar_one()
        busy_timeout = session.execute(text("PRAGMA busy_timeout")).scalar_one()

    assert str(journal_mode).lower() == "wal"
    assert int(busy_timeout) >= 120000
