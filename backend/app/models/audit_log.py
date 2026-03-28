from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, UUIDPrimaryKeyMixin, CreatedAtMixin


class AuditLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only audit log table (per D-08: no update/delete)."""

    __tablename__ = "audit_logs"

    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    actor_username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_role: Mapped[str] = mapped_column(String(20), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
