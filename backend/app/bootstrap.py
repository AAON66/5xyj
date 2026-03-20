from __future__ import annotations

from pathlib import Path

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import configure_logging


def ensure_runtime_directories(settings: Settings | None = None) -> list[Path]:
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


def bootstrap_application(settings: Settings | None = None) -> Settings:
    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings)
    ensure_runtime_directories(runtime_settings)
    return runtime_settings