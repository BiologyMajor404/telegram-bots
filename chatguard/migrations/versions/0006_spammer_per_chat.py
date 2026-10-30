"""Shared spammer list: one record per chat that caught the person, AI catches only

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
    op.add_column("spammers", sa.Column("chat_id", sa.BigInteger, nullable=True))
    # Each record goes to the chat whose AI caught the person last (that chat's Restore can
    # clear it); records the rules alone made are dropped, as the list now takes AI catches only
    op.execute(
        "UPDATE spammers SET chat_id = ("
        "SELECT i.chat_id FROM incidents i WHERE i.user_id = spammers.user_id "
        "AND i.source <> 'rules' AND NOT i.restored ORDER BY i.created_at DESC LIMIT 1)"
    )
    op.execute("DELETE FROM spammers WHERE chat_id IS NULL")
    op.alter_column("spammers", "chat_id", nullable=False)
    op.drop_constraint("spammers_pkey", "spammers", type_="primary")
    op.create_primary_key("spammers_pkey", "spammers", ["user_id", "chat_id"])


def downgrade() -> None:
    # Back to one record per person: keep the latest
    op.execute(
        "DELETE FROM spammers a USING spammers b WHERE a.user_id = b.user_id "
        "AND (a.last_caught_at, a.chat_id) < (b.last_caught_at, b.chat_id)"
    )
    op.drop_constraint("spammers_pkey", "spammers", type_="primary")
    op.drop_column("spammers", "chat_id")
    op.create_primary_key("spammers_pkey", "spammers", ["user_id"])
