from __future__ import annotations

import logging

from backend.app.core.config import Settings


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage().replace('"', '\\"')
        return (
            "{"
            f'"level":"{record.levelname}",' 
            f'"logger":"{record.name}",' 
            f'"message":"{message}"'
            "}"
        )


def configure_logging(settings: Settings) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level, logging.INFO))

    handler = logging.StreamHandler()
    if settings.log_format == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))

    root_logger.handlers.clear()
    root_logger.addHandler(handler)