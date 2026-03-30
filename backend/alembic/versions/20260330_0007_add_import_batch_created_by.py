"""Add created_by column to import_batches table."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260330_0007"
down_revision: Union[str, None] = "20260328_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "import_batches",
        sa.Column(
            "created_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_import_batches_created_by", "import_batches", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_import_batches_created_by", table_name="import_batches")
    op.drop_column("import_batches", "created_by")
