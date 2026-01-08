"""Add chapter_names to stories table

Revision ID: f1a2b3c4d5e6
Revises: e5f6g7h8i9j0_add_display_order_to_snippets
Create Date: 2026-01-08 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e5f6g7h8i9j0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add chapter_names JSON column to stories table for custom chapter labels."""
    op.add_column(
        "stories",
        sa.Column("chapter_names", sa.JSON(), nullable=True, server_default="{}")
    )


def downgrade() -> None:
    """Remove chapter_names column from stories table."""
    op.drop_column("stories", "chapter_names")
