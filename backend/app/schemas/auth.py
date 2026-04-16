from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AuthRole = Literal['admin', 'hr', 'employee']


class AuthUserRead(BaseModel):
    username: str
    role: AuthRole
    display_name: str
    must_change_password: bool = False
    feishu_bound: bool = False


class AuthLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)
    role: AuthRole = 'admin'  # kept for backward compat; ignored by backend


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: Literal['bearer'] = 'bearer'
    expires_at: datetime
    user: AuthUserRead


class EmployeeVerifyRequest(BaseModel):
    employee_id: str = Field(min_length=1, max_length=100)
    id_number: str = Field(min_length=1, max_length=100)
    person_name: str = Field(min_length=1, max_length=100)


class EmployeeVerifyResponse(BaseModel):
    access_token: str
    token_type: Literal['bearer'] = 'bearer'
    expires_at: datetime
    user: AuthUserRead


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)
