from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from backend.app.models.enums import MappingSource

if TYPE_CHECKING:
    from backend.app.models.source_file import SourceFile


class HeaderMapping(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "header_mappings"

    source_file_id: Mapped[str] = mapped_column(
        ForeignKey("source_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_header: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_header_signature: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    canonical_field: Mapped[str | None] = mapped_column(String(100), index=True)
    mapping_source: Mapped[MappingSource] = mapped_column(
        Enum(MappingSource, native_enum=False),
        nullable=False,
        default=MappingSource.RULE,
        index=True,
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    manually_overridden: Mapped[bool] = mapped_column(nullable=False, default=False)
    candidate_fields: Mapped[list[str] | None] = mapped_column(JSON)

    source_file: Mapped["SourceFile"] = relationship(back_populates="header_mappings")