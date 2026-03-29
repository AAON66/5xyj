"""Add region column to employee_master table."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260328_0006"
down_revision: Union[str, None] = "20260328_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employee_master",
        sa.Column("region", sa.String(50), nullable=True, index=True),
    )


def downgrade() -> None:
    op.drop_column("employee_master", "region")
