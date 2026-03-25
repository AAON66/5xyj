from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from backend.app.models.enums import EmployeeAuditAction

if TYPE_CHECKING:
    from backend.app.models.employee_master import EmployeeMaster


class EmployeeMasterAudit(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "employee_master_audits"

    employee_master_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("employee_master.id", ondelete="SET NULL"),
        index=True,
    )
    employee_id_snapshot: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[EmployeeAuditAction] = mapped_column(
        Enum(EmployeeAuditAction, native_enum=False),
        nullable=False,
        index=True,
    )
    note: Mapped[Optional[str]] = mapped_column(String(255))
    snapshot: Mapped[Optional[dict[str, object]]] = mapped_column(JSON)

    employee_master: Mapped["EmployeeMaster | None"] = relationship(back_populates="audits")
