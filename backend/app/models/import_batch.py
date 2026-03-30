from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.models.enums import BatchStatus

if TYPE_CHECKING:
    from backend.app.models.export_job import ExportJob
    from backend.app.models.match_result import MatchResult
    from backend.app.models.normalized_record import NormalizedRecord
    from backend.app.models.source_file import SourceFile
    from backend.app.models.user import User
    from backend.app.models.validation_issue import ValidationIssue


class ImportBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "import_batches"

    batch_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, native_enum=False),
        nullable=False,
        default=BatchStatus.UPLOADED,
        index=True,
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    creator: Mapped["User | None"] = relationship()

    source_files: Mapped[list["SourceFile"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    normalized_records: Mapped[list["NormalizedRecord"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    validation_issues: Mapped[list["ValidationIssue"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    match_results: Mapped[list["MatchResult"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    export_jobs: Mapped[list["ExportJob"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )