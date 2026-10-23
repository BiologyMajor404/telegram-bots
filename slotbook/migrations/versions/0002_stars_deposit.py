"""Telegram Stars deposit: payment fields on bookings, key-value settings

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bookings", sa.Column("deposit_stars", sa.Integer, nullable=False, server_default="0")
    )
    op.add_column("bookings", sa.Column("payment_charge_id", sa.String(128), nullable=True))
    op.add_column(
        "bookings",
        sa.Column("refunded", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.String(256), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_column("bookings", "refunded")
    op.drop_column("bookings", "payment_charge_id")
    op.drop_column("bookings", "deposit_stars")
