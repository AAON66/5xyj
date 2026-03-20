from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.models.match_result import MatchResult


class EmployeeMaster(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "employee_master"

    employee_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    person_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    id_number: Mapped[str | None] = mapped_column(String(100), index=True)
    company_name: Mapped[str | None] = mapped_column(String(255), index=True)
    department: Mapped[str | None] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(nullable=False, default=True, index=True)

    match_results: Mapped[list["MatchResult"]] = relationship(back_populates="employee_master")