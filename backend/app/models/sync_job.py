from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from backend.app.models.sync_config import SyncConfig


class SyncJob(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "sync_jobs"

    config_id: Mapped[str] = mapped_column(ForeignKey("sync_configs.id"), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # 'push' | 'pull'
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # status values: 'pending' | 'running' | 'success' | 'failed' | 'partial'
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    success_records: Mapped[int] = mapped_column(Integer, default=0)
    failed_records: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(String(2000))
    detail: Mapped[Optional[dict]] = mapped_column(JSON)
    triggered_by: Mapped[str] = mapped_column(String(100), nullable=False)

    config: Mapped["SyncConfig"] = relationship()
