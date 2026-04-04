from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class AnomalyRecordRead(BaseModel):
    id: str
    employee_identifier: str
    person_name: Optional[str] = None
    company_name: Optional[str] = None
    region: Optional[str] = None
    left_period: str
    right_period: str
    field_name: str
    left_value: Optional[str] = None
    right_value: Optional[str] = None
    change_percent: float
    threshold_percent: float
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AnomalyDetectRequest(BaseModel):
    left_period: str
    right_period: str
    thresholds: dict[str, float] = {}


class AnomalyStatusUpdateRequest(BaseModel):
    status: Literal["confirmed", "excluded"]
    anomaly_ids: list[str]


class AnomalyListRead(BaseModel):
    items: list[AnomalyRecordRead]
    total: int
    page: int
    page_size: int
