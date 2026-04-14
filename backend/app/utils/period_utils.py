from __future__ import annotations

from datetime import date, datetime
import re
from pathlib import Path
from typing import Any, Optional

COMPACT_DATE_PATTERN = re.compile(r"(?<!\d)(20\d{2})(0[1-9]|1[0-2])([0-2]\d|3[01])(?!\d)")
TEXT_DATE_PATTERN = re.compile(
    r"(?<!\d)(20\d{2})\s*(?:年|[-/._])\s*(0?[1-9]|1[0-2])\s*(?:月|[-/._])\s*(0?[1-9]|[12]\d|3[01])(?:日)?"
)
COMPACT_PERIOD_PATTERN = re.compile(r"(?<!\d)(20\d{2})(0[1-9]|1[0-2])(?!\d)")
TEXT_PERIOD_PATTERN = re.compile(
    r"(?<!\d)(20\d{2})\s*(?:年|[-/._])?\s*-?\s*(0?[1-9]|1[0-2])(?:月)?"
)


def normalize_billing_period(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m")
    if isinstance(value, date):
        return value.strftime("%Y-%m")

    text = str(value).strip()
    if not text:
        return None

    for pattern in (COMPACT_PERIOD_PATTERN, TEXT_PERIOD_PATTERN):
        match = pattern.search(text)
        if match is None:
            continue
        year, month = match.groups()
        return f"{year}-{month.zfill(2)}"

    return None


def normalize_period_boundary(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    if not text:
        return None

    for pattern in (COMPACT_DATE_PATTERN, TEXT_DATE_PATTERN):
        match = pattern.search(text)
        if match is None:
            continue
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    return None


def infer_billing_period_from_filename(filename: str | None) -> Optional[str]:
    if not filename:
        return None
    return normalize_billing_period(Path(filename).stem)


def coalesce_billing_period(*candidates: Any) -> Optional[str]:
    for candidate in candidates:
        normalized = normalize_billing_period(candidate)
        if normalized:
            return normalized
    return None
