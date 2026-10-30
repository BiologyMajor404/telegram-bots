"""Gifted Pro in a column of its own; room for longer source names

Revision ID: 0007
Revises: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A gift used to be a Pro "until 2100" with "gift" in place of the payment, so the
    # renewal of a real subscription overwrote it
    op.add_column(
        "subscribers", sa.Column("gift", sa.Boolean, nullable=False, server_default=sa.false())
    )
    op.execute(
        "UPDATE subscribers SET gift = true, pro_until = NULL, pro_charge_id = NULL "
        "WHERE pro_charge_id = 'gift'"
    )
    # "Telegram @<32 letters>", a feed's host or a letter's sender didn't fit into 32
    op.alter_column("jobs", "source", type_=sa.String(128))


def downgrade() -> None:
    op.alter_column("jobs", "source", type_=sa.String(32), postgresql_using="left(source, 32)")
    op.execute("UPDATE subscribers SET pro_until = '2100-01-01', pro_charge_id = 'gift' WHERE gift")
    op.drop_column("subscribers", "gift")
