from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, UUIDPrimaryKeyMixin
from backend.app.models.enums import SourceFileKind

if TYPE_CHECKING:
    from backend.app.models.header_mapping import HeaderMapping
    from backend.app.models.import_batch import ImportBatch
    from backend.app.models.normalized_record import NormalizedRecord


class SourceFile(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "source_files"

    batch_id: Mapped[str] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_kind: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=SourceFileKind.SOCIAL_SECURITY.value,
        server_default=SourceFileKind.SOCIAL_SECURITY.value,
        index=True,
    )
    region: Mapped[Optional[str]] = mapped_column(String(100))
    company_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    raw_sheet_name: Mapped[Optional[str]] = mapped_column(String(255))
    file_hash: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    batch: Mapped["ImportBatch"] = relationship(back_populates="source_files")
    header_mappings: Mapped[list["HeaderMapping"]] = relationship(
        back_populates="source_file",
        cascade="all, delete-orphan",
    )
    normalized_records: Mapped[list["NormalizedRecord"]] = relationship(
        back_populates="source_file",
        cascade="all, delete-orphan",
    )
