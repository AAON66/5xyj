from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Float, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class AnomalyRecord(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Persisted anomaly detection result for cross-period comparison."""

    __tablename__ = "anomaly_records"
    __table_args__ = (
        UniqueConstraint(
            "employee_identifier", "left_period", "right_period", "field_name",
            name="uq_anomaly_identity",
        ),
    )

    employee_identifier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    person_name: Mapped[Optional[str]] = mapped_column(String(255))
    company_name: Mapped[Optional[str]] = mapped_column(String(255))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    left_period: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    right_period: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    left_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    right_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    change_percent: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_percent: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
