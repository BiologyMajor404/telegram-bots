"""Initial schema: chats, members, expenses, shares, settlements

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
        sa.Column("currency", sa.String(8), nullable=False),
    )
    op.create_table(
        "members",
        sa.Column("chat_id", sa.BigInteger, sa.ForeignKey("chats.id"), primary_key=True),
        sa.Column("user_id", sa.BigInteger, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column(
            "joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chat_id", sa.BigInteger, sa.ForeignKey("chats.id"), nullable=False, index=True),
        sa.Column("payer_id", sa.BigInteger, nullable=False),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("description", sa.String(128), nullable=False),
        sa.Column("is_deleted", sa.Boolean, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "shares",
        sa.Column("expense_id", sa.Integer, sa.ForeignKey("expenses.id"), primary_key=True),
        sa.Column("user_id", sa.BigInteger, primary_key=True),
        sa.Column("amount", sa.Integer, nullable=False),
    )
    op.create_table(
        "settlements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chat_id", sa.BigInteger, sa.ForeignKey("chats.id"), nullable=False, index=True),
        sa.Column("from_id", sa.BigInteger, nullable=False),
        sa.Column("to_id", sa.BigInteger, nullable=False),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    for table in ("settlements", "shares", "expenses", "members", "chats"):
        op.drop_table(table)
