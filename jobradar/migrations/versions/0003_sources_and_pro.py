"""Own sources by link, per-user daily limits, Pro subscription

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
    op.add_column("subscribers", sa.Column("pro_until", sa.DateTime(timezone=True)))
    op.add_column("subscribers", sa.Column("pro_charge_id", sa.String(256)))
    op.create_table(
        "user_sources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("ref", sa.String(512), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", "kind", "ref"),
    )
    op.create_table(
        "user_days",
        sa.Column("user_id", sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column("day", sa.Date, primary_key=True),
        sa.Column("cards", sa.Integer, nullable=False),
        sa.Column("checks", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_days")
    op.drop_table("user_sources")
    op.drop_column("subscribers", "pro_charge_id")
    op.drop_column("subscribers", "pro_until")
