"""Add Feishu sync models (sync_configs, sync_jobs) and user Feishu OAuth columns."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260401_0008"
down_revision: Union[str, None] = "20260330_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sync_configs table
    op.create_table(
        "sync_configs",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("app_token", sa.String(255), nullable=False),
        sa.Column("table_id", sa.String(255), nullable=False),
        sa.Column("granularity", sa.String(20), nullable=False),
        sa.Column("field_mapping", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create sync_jobs table
    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("config_id", sa.Uuid(as_uuid=False), sa.ForeignKey("sync_configs.id"), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("total_records", sa.Integer, default=0),
        sa.Column("success_records", sa.Integer, default=0),
        sa.Column("failed_records", sa.Integer, default=0),
        sa.Column("error_message", sa.String(2000), nullable=True),
        sa.Column("detail", sa.JSON, nullable=True),
        sa.Column("triggered_by", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sync_jobs_config_id", "sync_jobs", ["config_id"])
    op.create_index("ix_sync_jobs_status", "sync_jobs", ["status"])

    # Add Feishu OAuth columns to users table
    op.add_column("users", sa.Column("feishu_open_id", sa.String(100), nullable=True, unique=True))
    op.add_column("users", sa.Column("feishu_union_id", sa.String(100), nullable=True))
    op.create_index("ix_users_feishu_open_id", "users", ["feishu_open_id"])


def downgrade() -> None:
    op.drop_index("ix_users_feishu_open_id", table_name="users")
    op.drop_column("users", "feishu_union_id")
    op.drop_column("users", "feishu_open_id")
    op.drop_index("ix_sync_jobs_status", table_name="sync_jobs")
    op.drop_index("ix_sync_jobs_config_id", table_name="sync_jobs")
    op.drop_table("sync_jobs")
    op.drop_table("sync_configs")
