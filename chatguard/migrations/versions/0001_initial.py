"""Initial schema: chats, members, incidents

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chats",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("lang", sa.String(8), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("checked", sa.Integer, nullable=False),
        sa.Column("caught", sa.Integer, nullable=False),
        sa.Column("ai_day", sa.Date, nullable=True),
        sa.Column("ai_checks", sa.Integer, nullable=False),
    )
    op.create_table(
        "members",
        sa.Column("chat_id", sa.BigInteger, sa.ForeignKey("chats.id"), primary_key=True),
        sa.Column("user_id", sa.BigInteger, primary_key=True),
        sa.Column("clean_messages", sa.Integer, nullable=False),
        sa.Column("trusted", sa.Boolean, nullable=False),
    )
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chat_id", sa.BigInteger, sa.ForeignKey("chats.id"), nullable=False, index=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("user_name", sa.String(128), nullable=False),
        sa.Column("text", sa.String(4096), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("reason", sa.String(512), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("restored", sa.Boolean, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    for table in ("incidents", "members", "chats"):
        op.drop_table(table)
