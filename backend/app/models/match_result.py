from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from backend.app.models.enums import MatchStatus

if TYPE_CHECKING:
    from backend.app.models.employee_master import EmployeeMaster
    from backend.app.models.import_batch import ImportBatch
    from backend.app.models.normalized_record import NormalizedRecord


class MatchResult(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "match_results"
    __table_args__ = (UniqueConstraint("normalized_record_id", name="uq_match_results_normalized_record_id"),)

    batch_id: Mapped[str] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    normalized_record_id: Mapped[str] = mapped_column(
        ForeignKey("normalized_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_master_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("employee_master.id", ondelete="SET NULL"),
        index=True,
    )
    match_status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, native_enum=False),
        nullable=False,
        default=MatchStatus.UNMATCHED,
        index=True,
    )
    match_basis: Mapped[Optional[str]] = mapped_column(String(255))
    confidence: Mapped[Optional[float]] = mapped_column(Float)

    batch: Mapped["ImportBatch"] = relationship(back_populates="match_results")
    normalized_record: Mapped["NormalizedRecord"] = relationship(back_populates="match_results")
    employee_master: Mapped["EmployeeMaster | None"] = relationship(back_populates="match_results")