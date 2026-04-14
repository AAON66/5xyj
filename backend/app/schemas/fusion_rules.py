from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


FusionRuleScopeType = Literal["employee_id", "id_number"]
FusionRuleFieldName = Literal["personal_social_burden", "personal_housing_burden"]


class FusionRuleCreate(BaseModel):
    scope_type: FusionRuleScopeType
    scope_value: str = Field(..., min_length=1, max_length=100)
    field_name: FusionRuleFieldName
    override_value: Decimal
    note: Optional[str] = Field(default=None, max_length=255)


class FusionRuleUpdate(BaseModel):
    scope_type: Optional[FusionRuleScopeType] = None
    scope_value: Optional[str] = Field(default=None, min_length=1, max_length=100)
    field_name: Optional[FusionRuleFieldName] = None
    override_value: Optional[Decimal] = None
    note: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class FusionRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scope_type: FusionRuleScopeType
    scope_value: str
    field_name: FusionRuleFieldName
    override_value: Decimal
    note: Optional[str]
    is_active: bool
    created_by: Optional[str]
    created_at: Union[str, datetime]
    updated_at: Union[str, datetime]


class FusionRuleListQuery(BaseModel):
    is_active: Optional[bool] = None
    field_name: Optional[FusionRuleFieldName] = None
