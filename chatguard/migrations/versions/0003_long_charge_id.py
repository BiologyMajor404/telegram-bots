"""Subscription payment charge ids are longer than 128 characters

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
    op.alter_column("chats", "pro_charge_id", type_=sa.String(512), existing_nullable=True)


def downgrade() -> None:
    op.alter_column("chats", "pro_charge_id", type_=sa.String(128), existing_nullable=True)
