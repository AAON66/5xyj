from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class FusionBurdenRow(BaseModel):
    employee_id: str | None = None
    id_number: str | None = None
    personal_social_burden: Decimal | None = None
    personal_housing_burden: Decimal | None = None
    source_kind: Literal["excel", "feishu"]
    source_ref: str


class FusionBurdenDiagnostics(BaseModel):
    missing_key_rows: int = 0
    duplicate_key_rows: int = 0
    unmatched_rows: int = 0
    messages: list[str] = []
