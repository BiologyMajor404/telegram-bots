"""Pro subscription fields and the shared spammer list

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
    op.add_column("chats", sa.Column("pro_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("chats", sa.Column("pro_owner_id", sa.BigInteger, nullable=True))
    op.add_column("chats", sa.Column("pro_charge_id", sa.String(128), nullable=True))
    op.create_table(
        "spammers",
        sa.Column("user_id", sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column("caught", sa.Integer, nullable=False),
        sa.Column(
            "last_caught_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("spammers")
    op.drop_column("chats", "pro_charge_id")
    op.drop_column("chats", "pro_owner_id")
    op.drop_column("chats", "pro_until")
