"""Add fusion_rules table for persisted aggregate overrides."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260409_0010"
down_revision: Union[str, None] = "20260404_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fusion_rules",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("scope_type", sa.String(20), nullable=False),
        sa.Column("scope_value", sa.String(100), nullable=False),
        sa.Column("field_name", sa.String(64), nullable=False),
        sa.Column("override_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "scope_type in ('employee_id', 'id_number')",
            name="ck_fusion_rules_scope_type_allowed",
        ),
        sa.CheckConstraint(
            "field_name in ('personal_social_burden', 'personal_housing_burden')",
            name="ck_fusion_rules_field_name_allowed",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_fusion_rules"),
    )
    op.create_index("ix_fusion_rules_scope_value", "fusion_rules", ["scope_value"])
    op.create_index("ix_fusion_rules_field_name", "fusion_rules", ["field_name"])
    op.create_index("ix_fusion_rules_is_active", "fusion_rules", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_fusion_rules_is_active", table_name="fusion_rules")
    op.drop_index("ix_fusion_rules_field_name", table_name="fusion_rules")
    op.drop_index("ix_fusion_rules_scope_value", table_name="fusion_rules")
    op.drop_table("fusion_rules")
