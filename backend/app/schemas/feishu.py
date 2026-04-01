from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field


# --- SyncConfig schemas ---


class SyncConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    app_token: str = Field(..., min_length=1, max_length=255)
    table_id: str = Field(..., min_length=1, max_length=255)
    granularity: str = Field(..., pattern=r'^(detail|summary)$')
    field_mapping: dict[str, str] = Field(default_factory=dict)


class SyncConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    app_token: Optional[str] = Field(None, min_length=1, max_length=255)
    table_id: Optional[str] = Field(None, min_length=1, max_length=255)
    granularity: Optional[str] = Field(None, pattern=r'^(detail|summary)$')
    field_mapping: Optional[dict[str, str]] = None
    is_active: Optional[bool] = None


class SyncConfigRead(BaseModel):
    id: str
    name: str
    app_token: str
    table_id: str
    granularity: str
    field_mapping: dict[str, str]
    is_active: bool
    created_at: Union[str, datetime]
    updated_at: Union[str, datetime]

    model_config = {"from_attributes": True}


# --- SyncJob schemas ---


class SyncJobRead(BaseModel):
    id: str
    config_id: str
    direction: str
    status: str
    total_records: int
    success_records: int
    failed_records: int
    error_message: Optional[str]
    detail: Optional[dict]
    triggered_by: str
    created_at: Union[str, datetime]

    model_config = {"from_attributes": True}


# --- Push/Pull request schemas ---


class PushRequest(BaseModel):
    config_id: str
    filters: Optional[dict] = None  # optional: region, company_name, billing_period


class PullRequest(BaseModel):
    config_id: str


class ConflictRecord(BaseModel):
    record_key: str  # "{id_number}_{billing_period}"
    person_name: Optional[str]
    system_values: dict[str, object]
    feishu_values: dict[str, object]
    diff_fields: list[str]


class ConflictPreview(BaseModel):
    total_conflicts: int
    conflicts: list[ConflictRecord]


class ConflictResolution(BaseModel):
    config_id: str
    strategy: str = Field(..., pattern=r'^(system_wins|feishu_wins|per_record)$')
    per_record_choices: Optional[dict[str, str]] = None  # {record_key: 'system'|'feishu'}


class PushConflictAction(BaseModel):
    config_id: str
    action: str = Field(..., pattern=r'^(overwrite|skip|cancel)$')
    record_keys: Optional[list[str]] = None  # specific keys to overwrite/skip


# --- Settings schemas ---


class FeishuCredentials(BaseModel):
    app_id: str = Field(..., min_length=1)
    app_secret: str = Field(..., min_length=1)


class FeatureFlags(BaseModel):
    feishu_sync_enabled: bool
    feishu_oauth_enabled: bool
    feishu_credentials_configured: bool


# --- Feishu field discovery ---


class FeishuFieldInfo(BaseModel):
    field_id: str
    field_name: str
    field_type: int
    description: Optional[str] = None
