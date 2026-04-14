from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import TimestampMixin, UUIDPrimaryKeyMixin, Base


AMOUNT_TYPE = Numeric(12, 2)


class FusionRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fusion_rules"
    __table_args__ = (
        CheckConstraint(
            "scope_type in ('employee_id', 'id_number')",
            name="ck_fusion_rules_scope_type_allowed",
        ),
        CheckConstraint(
            "field_name in ('personal_social_burden', 'personal_housing_burden')",
            name="ck_fusion_rules_field_name_allowed",
        ),
    )

    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    scope_value: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    override_value: Mapped[Decimal] = mapped_column(AMOUNT_TYPE, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
