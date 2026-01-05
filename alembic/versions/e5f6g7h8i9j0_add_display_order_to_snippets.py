"""Add display_order to snippets table

Revision ID: e5f6g7h8i9j0
Revises: d8e9f0a1b2c3
Create Date: 2024-12-22 10:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e5f6g7h8i9j0"
down_revision = "d8e9f0a1b2c3"
branch_labels = None
depends_on = None


def upgrade():
    # Add display_order column to snippets table
    op.add_column(
        "snippets",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("snippets", "display_order")
