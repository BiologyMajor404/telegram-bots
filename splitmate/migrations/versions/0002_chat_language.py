"""Per-chat interface language

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
    op.add_column("chats", sa.Column("lang", sa.String(8), nullable=False, server_default="ru"))


def downgrade() -> None:
    op.drop_column("chats", "lang")
