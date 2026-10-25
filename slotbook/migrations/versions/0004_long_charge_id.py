"""Telegram payment charge ids can be longer than 128 characters

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
    op.alter_column("bookings", "payment_charge_id", type_=sa.String(512), existing_nullable=True)


def downgrade() -> None:
    op.alter_column("bookings", "payment_charge_id", type_=sa.String(128), existing_nullable=True)
