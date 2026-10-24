"""Custom amounts per person in an expense

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shares", sa.Column("fixed", sa.Boolean, nullable=False, server_default=sa.false())
    )


def downgrade() -> None:
    op.drop_column("shares", "fixed")
