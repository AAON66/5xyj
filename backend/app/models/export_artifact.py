from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from backend.app.models.enums import TemplateType

if TYPE_CHECKING:
    from backend.app.models.export_job import ExportJob


class ExportArtifact(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "export_artifacts"
    __table_args__ = (UniqueConstraint("export_job_id", "template_type", name="uq_export_artifacts_job_template"),)

    export_job_id: Mapped[str] = mapped_column(
        ForeignKey("export_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_type: Mapped[TemplateType] = mapped_column(
        Enum(TemplateType, native_enum=False),
        nullable=False,
        index=True,
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    export_job: Mapped["ExportJob"] = relationship(back_populates="artifacts")