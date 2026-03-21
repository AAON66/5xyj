"""Add employee master audit trail and update timestamps."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260321_0003"
down_revision: Union[str, None] = "20260320_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("employee_master") as batch_op:
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )

    op.create_table(
        "employee_master_audits",
        sa.Column("employee_master_id", sa.Uuid(as_uuid=False), nullable=True),
        sa.Column("employee_id_snapshot", sa.String(length=100), nullable=False),
        sa.Column("action", sa.Enum("IMPORT_CREATE", "IMPORT_UPDATE", "MANUAL_UPDATE", "STATUS_CHANGE", "DELETE", name="employeeauditaction", native_enum=False), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["employee_master_id"], ["employee_master.id"], name=op.f("fk_employee_master_audits_employee_master_id_employee_master"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_master_audits")),
    )
    op.create_index(op.f("ix_employee_master_audits_action"), "employee_master_audits", ["action"], unique=False)
    op.create_index(op.f("ix_employee_master_audits_employee_id_snapshot"), "employee_master_audits", ["employee_id_snapshot"], unique=False)
    op.create_index(op.f("ix_employee_master_audits_employee_master_id"), "employee_master_audits", ["employee_master_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_employee_master_audits_employee_master_id"), table_name="employee_master_audits")
    op.drop_index(op.f("ix_employee_master_audits_employee_id_snapshot"), table_name="employee_master_audits")
    op.drop_index(op.f("ix_employee_master_audits_action"), table_name="employee_master_audits")
    op.drop_table("employee_master_audits")

    with op.batch_alter_table("employee_master") as batch_op:
        batch_op.drop_column("updated_at")
