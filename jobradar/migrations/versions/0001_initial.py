"""Initial schema: subscribers, jobs, ai_usage

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
        "subscribers",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column("lang", sa.String(8), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False),
        sa.Column("only_top", sa.Boolean, nullable=False),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("external_id", sa.String(128), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("niche", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(512), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("source", "external_id"),
    )
    op.create_table(
        "ai_usage",
        sa.Column("day", sa.Date, primary_key=True),
        sa.Column("checks", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    for table in ("ai_usage", "jobs", "subscribers"):
        op.drop_table(table)
