from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.models.employee_master_audit import EmployeeMasterAudit
    from backend.app.models.match_result import MatchResult


class EmployeeMaster(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employee_master"

    employee_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    person_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    id_number: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    department: Mapped[Optional[str]] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(nullable=False, default=True, index=True)

    match_results: Mapped[list["MatchResult"]] = relationship(back_populates="employee_master")
    audits: Mapped[list["EmployeeMasterAudit"]] = relationship(
        back_populates="employee_master",
        order_by=lambda: _employee_master_audit_ordering(),
    )


def _employee_master_audit_ordering():
    from backend.app.models.employee_master_audit import EmployeeMasterAudit

    return EmployeeMasterAudit.created_at.desc(), EmployeeMasterAudit.id.desc()
