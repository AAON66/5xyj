from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.models.import_batch import ImportBatch
    from backend.app.models.match_result import MatchResult
    from backend.app.models.source_file import SourceFile
    from backend.app.models.validation_issue import ValidationIssue


AMOUNT_TYPE = Numeric(12, 2)


class NormalizedRecord(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "normalized_records"

    batch_id: Mapped[str] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_file_id: Mapped[str] = mapped_column(
        ForeignKey("source_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    person_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    id_type: Mapped[Optional[str]] = mapped_column(String(100))
    id_number: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    employee_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    social_security_number: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    region: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    billing_period: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    period_start: Mapped[Optional[str]] = mapped_column(String(100))
    period_end: Mapped[Optional[str]] = mapped_column(String(100))
    payment_base: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    payment_salary: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    housing_fund_account: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    housing_fund_base: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    housing_fund_personal: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    housing_fund_company: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    housing_fund_total: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    total_amount: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    company_total_amount: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    personal_total_amount: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    pension_company: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    pension_personal: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    medical_company: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    medical_personal: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    medical_maternity_company: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    maternity_amount: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    unemployment_company: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    unemployment_personal: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    injury_company: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    supplementary_medical_company: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    supplementary_pension_company: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    large_medical_personal: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    late_fee: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    interest: Mapped[Optional[Decimal]] = mapped_column(AMOUNT_TYPE)
    raw_sheet_name: Mapped[Optional[str]] = mapped_column(String(255))
    raw_header_signature: Mapped[Optional[str]] = mapped_column(String(500))
    source_file_name: Mapped[Optional[str]] = mapped_column(String(255))
    raw_payload: Mapped[Optional[dict[str, object]]] = mapped_column(JSON)

    batch: Mapped["ImportBatch"] = relationship(back_populates="normalized_records")
    source_file: Mapped["SourceFile"] = relationship(back_populates="normalized_records")
    validation_issues: Mapped[list["ValidationIssue"]] = relationship(
        back_populates="normalized_record",
        cascade="all, delete-orphan",
    )
    match_results: Mapped[list["MatchResult"]] = relationship(
        back_populates="normalized_record",
        cascade="all, delete-orphan",
    )
