from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: str
    action: str
    actor_username: str
    actor_role: str
    ip_address: Optional[str] = None
    detail: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    success: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: list[AuditLogRead]
    total: int
    page: int
    page_size: int
