"""Per-user interface language

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
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column("lang", sa.String(8), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("users")
