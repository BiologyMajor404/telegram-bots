"""Global daily AI usage counter

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_usage",
        sa.Column("day", sa.Date, primary_key=True),
        sa.Column("checks", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ai_usage")
