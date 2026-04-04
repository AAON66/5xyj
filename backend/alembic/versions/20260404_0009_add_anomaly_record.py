"""Add anomaly_records table for cross-period anomaly detection."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260404_0009"
down_revision: Union[str, None] = "20260401_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "anomaly_records",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("employee_identifier", sa.String(100), nullable=False),
        sa.Column("person_name", sa.String(255), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("left_period", sa.String(100), nullable=False),
        sa.Column("right_period", sa.String(100), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("left_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("right_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("change_percent", sa.Float, nullable=False),
        sa.Column("threshold_percent", sa.Float, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", sa.String(100), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_anomaly_records"),
        sa.UniqueConstraint(
            "employee_identifier", "left_period", "right_period", "field_name",
            name="uq_anomaly_identity",
        ),
    )
    op.create_index("ix_anomaly_records_employee_identifier", "anomaly_records", ["employee_identifier"])
    op.create_index("ix_anomaly_records_left_period", "anomaly_records", ["left_period"])
    op.create_index("ix_anomaly_records_right_period", "anomaly_records", ["right_period"])


def downgrade() -> None:
    op.drop_index("ix_anomaly_records_right_period", table_name="anomaly_records")
    op.drop_index("ix_anomaly_records_left_period", table_name="anomaly_records")
    op.drop_index("ix_anomaly_records_employee_identifier", table_name="anomaly_records")
    op.drop_table("anomaly_records")
