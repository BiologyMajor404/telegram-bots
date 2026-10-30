"""Participants can leave: new expenses skip them, their balance and history stay

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "members", sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true())
    )


def downgrade() -> None:
    op.drop_column("members", "active")
