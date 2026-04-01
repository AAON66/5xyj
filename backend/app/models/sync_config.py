from __future__ import annotations

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SyncConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sync_configs"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    app_token: Mapped[str] = mapped_column(String(255), nullable=False)
    table_id: Mapped[str] = mapped_column(String(255), nullable=False)
    granularity: Mapped[str] = mapped_column(String(20), nullable=False)  # 'detail' | 'summary'
    field_mapping: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
