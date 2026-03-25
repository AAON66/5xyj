from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.models.export_artifact import ExportArtifact
    from backend.app.models.import_batch import ImportBatch


class ExportJob(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "export_jobs"

    batch_id: Mapped[str] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    batch: Mapped["ImportBatch"] = relationship(back_populates="export_jobs")
    artifacts: Mapped[list["ExportArtifact"]] = relationship(
        back_populates="export_job",
        cascade="all, delete-orphan",
    )