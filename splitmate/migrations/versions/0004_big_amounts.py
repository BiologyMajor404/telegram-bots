"""Amounts in minor units can exceed 32 bits (21 million in a currency is 2^31 kopecks)

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

AMOUNT_COLUMNS = (("expenses", "amount"), ("shares", "amount"), ("settlements", "amount"))


def upgrade() -> None:
    for table, column in AMOUNT_COLUMNS:
        op.alter_column(table, column, type_=sa.BigInteger, existing_nullable=False)


def downgrade() -> None:
    for table, column in AMOUNT_COLUMNS:
        op.alter_column(table, column, type_=sa.Integer, existing_nullable=False)
