from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AuthRole = Literal['admin', 'hr']


class AuthUserRead(BaseModel):
    username: str
    role: AuthRole
    display_name: str


class AuthLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)
    role: AuthRole


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: Literal['bearer'] = 'bearer'
    expires_at: datetime
    user: AuthUserRead
