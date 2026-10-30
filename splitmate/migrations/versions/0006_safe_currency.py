"""Reset currencies with HTML markup, saved before /currency checked its argument

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A currency like "<b" or "&" breaks every message with an amount in it. Such chats get
    # their language's default, as in texts.py: $ for English, zł for Polish, ₴ otherwise
    op.execute(
        sa.text(
            "UPDATE chats SET currency = CASE lang WHEN 'en' THEN '$' WHEN 'pl' THEN 'zł' "
            "ELSE '₴' END WHERE currency ~ '[<>&]'"
        )
    )


def downgrade() -> None:
    pass  # the old values broke the chat's messages anyway
