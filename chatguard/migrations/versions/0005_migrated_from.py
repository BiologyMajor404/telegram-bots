"""Remember which group a supergroup was migrated from

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
    op.add_column("chats", sa.Column("migrated_from", sa.BigInteger, nullable=True))
    op.create_index("ix_chats_migrated_from", "chats", ["migrated_from"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_chats_migrated_from", table_name="chats")
    op.drop_column("chats", "migrated_from")
