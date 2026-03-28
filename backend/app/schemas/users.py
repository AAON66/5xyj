from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=200)
    role: Literal["admin", "hr"] = "hr"
    display_name: str = Field(default="", max_length=255)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=100)
    role: Optional[Literal["admin", "hr"]] = None
    display_name: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class UserPasswordReset(BaseModel):
    new_password: str = Field(min_length=8, max_length=200)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    role: str
    display_name: str
    is_active: bool
    must_change_password: bool
    created_at: datetime
    updated_at: datetime
