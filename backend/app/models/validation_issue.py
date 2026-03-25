from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.models.import_batch import ImportBatch
    from backend.app.models.normalized_record import NormalizedRecord


class ValidationIssue(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "validation_issues"

    batch_id: Mapped[str] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    normalized_record_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("normalized_records.id", ondelete="CASCADE"),
        index=True,
    )
    issue_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    field_name: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(nullable=False, default=False, index=True)

    batch: Mapped["ImportBatch"] = relationship(back_populates="validation_issues")
    normalized_record: Mapped["NormalizedRecord | None"] = relationship(back_populates="validation_issues")