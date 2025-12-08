"""Add summaries table only

Revision ID: 35c3ce144bee
Revises: 5abab21711bd
Create Date: 2025-12-08 00:31:05.596261

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "35c3ce144bee"
down_revision: Union[str, Sequence[str], None] = "5abab21711bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create summaries table
    op.create_table(
        "summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("story_id", sa.Integer(), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_final", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["story_id"],
            ["stories.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_summaries_id"), "summaries", ["id"], unique=False)
    op.create_index(
        op.f("ix_summaries_story_id"), "summaries", ["story_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_summaries_story_id"), table_name="summaries")
    op.drop_index(op.f("ix_summaries_id"), table_name="summaries")
    op.drop_table("summaries")
