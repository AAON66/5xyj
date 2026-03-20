"""Add file size metadata to source files."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260320_0002"
down_revision: Union[str, None] = "20260320_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("source_files") as batch_op:
        batch_op.add_column(sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("source_files") as batch_op:
        batch_op.drop_column("file_size")