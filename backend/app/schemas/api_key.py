from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="API Key 名称")
    owner_id: str = Field(description="绑定用户 ID")


class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str  # raw key, shown only once
    key_prefix: str
    owner_username: str
    owner_role: str
    created_at: datetime


class ApiKeyRead(BaseModel):
    id: str
    name: str
    key_prefix: str
    owner_id: str
    owner_username: str
    owner_role: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApiKeyListResponse(BaseModel):
    items: list[ApiKeyRead]
    total: int
