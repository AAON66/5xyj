from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import configure_logging

logger = logging.getLogger(__name__)


class UnsafeAuthConfigurationError(RuntimeError):
    """Raised when a non-local runtime is configured with unsafe auth defaults."""


def ensure_runtime_directories(settings: Optional[Settings] = None) -> list[Path]:
    runtime_settings = settings or get_settings()
    paths = [
        runtime_settings.upload_path,
        runtime_settings.samples_path,
        runtime_settings.templates_path,
        runtime_settings.outputs_path,
    ]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
    return paths


def validate_auth_runtime_guardrails(settings: Optional[Settings] = None) -> Settings:
    runtime_settings = settings or get_settings()
    if not runtime_settings.auth_enabled or runtime_settings.is_local_runtime:
        return runtime_settings

    issues: list[str] = []
    if runtime_settings.uses_default_admin_password:
        issues.append('`admin_login_password` is still using the shipped default.')
    if runtime_settings.uses_default_hr_password:
        issues.append('`hr_login_password` is still using the shipped default.')
    if runtime_settings.uses_unsafe_auth_secret_key:
        issues.append('`auth_secret_key` is still using a default or blocked unsafe placeholder.')

    if issues:
        issue_summary = ' '.join(issues)
        raise UnsafeAuthConfigurationError(
            f"Unsafe auth configuration blocked for runtime_environment="
            f"'{runtime_settings.normalized_runtime_environment}'. {issue_summary} "
            "Set non-default admin/hr credentials and a strong auth_secret_key, "
            "or keep runtime_environment='local' for local development only."
        )

    return runtime_settings


def _seed_default_admin_on_startup() -> None:
    """Seed the default admin user into the database if none exists."""
    from backend.app.core.database import get_db_session
    from backend.app.services.user_service import seed_default_admin

    gen = get_db_session()
    db = next(gen)
    try:
        seed_default_admin(db)
    except Exception:
        logger.exception("Failed to seed default admin user.")
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


def _ensure_tables() -> None:
    """Create any missing tables (e.g. audit_logs added in Phase 3)."""
    from backend.app.core.database import engine
    from backend.app.models.base import Base
    # Import all models so Base.metadata knows about them
    import backend.app.models  # noqa: F401

    Base.metadata.create_all(engine, checkfirst=True)


def bootstrap_application(settings: Optional[Settings] = None) -> Settings:
    runtime_settings = settings or get_settings()
    validate_auth_runtime_guardrails(runtime_settings)
    configure_logging(runtime_settings)
    ensure_runtime_directories(runtime_settings)
    _ensure_tables()
    _seed_default_admin_on_startup()
    return runtime_settings
