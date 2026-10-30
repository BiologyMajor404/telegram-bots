"""Remember a refund that is owed until Telegram confirms it, so a failed one is retried

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
    # Existing bookings start as not owed: a deposit kept after a late cancellation
    # must never be refunded by the retry
    op.add_column(
        "bookings",
        sa.Column("refund_owed", sa.Boolean, nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("bookings", "refund_owed")
