"""Add audit_logs table for security hardening."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260328_0005"
down_revision: Union[str, None] = "20260321_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("actor_username", sa.String(100), nullable=False, index=True),
        sa.Column("actor_role", sa.String(20), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("success", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
