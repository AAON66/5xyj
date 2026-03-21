"""Add housing fund support fields and source file kinds."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260321_0004"
down_revision: Union[str, None] = "20260321_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("source_files") as batch_op:
        batch_op.add_column(
            sa.Column(
                "source_kind",
                sa.String(length=50),
                nullable=False,
                server_default="social_security",
            )
        )
        batch_op.create_index(op.f("ix_source_files_source_kind"), ["source_kind"], unique=False)

    with op.batch_alter_table("normalized_records") as batch_op:
        batch_op.add_column(sa.Column("housing_fund_account", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("housing_fund_base", sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column("housing_fund_personal", sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column("housing_fund_company", sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column("housing_fund_total", sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.create_index(op.f("ix_normalized_records_housing_fund_account"), ["housing_fund_account"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("normalized_records") as batch_op:
        batch_op.drop_index(op.f("ix_normalized_records_housing_fund_account"))
        batch_op.drop_column("housing_fund_total")
        batch_op.drop_column("housing_fund_company")
        batch_op.drop_column("housing_fund_personal")
        batch_op.drop_column("housing_fund_base")
        batch_op.drop_column("housing_fund_account")

    with op.batch_alter_table("source_files") as batch_op:
        batch_op.drop_index(op.f("ix_source_files_source_kind"))
        batch_op.drop_column("source_kind")
