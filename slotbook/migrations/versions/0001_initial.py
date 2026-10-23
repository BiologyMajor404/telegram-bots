"""Initial schema: services, working hours, bookings

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
        "services",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("duration_min", sa.Integer, nullable=False),
        sa.Column("price", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False),
    )
    op.create_table(
        "work_days",
        sa.Column("weekday", sa.Integer, primary_key=True, autoincrement=False),
        sa.Column("start", sa.Time, nullable=True),
        sa.Column("end", sa.Time, nullable=True),
    )
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("user_name", sa.String(128), nullable=False),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("service_id", sa.Integer, sa.ForeignKey("services.id"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reminded_24h", sa.Boolean, nullable=False),
        sa.Column("reminded_2h", sa.Boolean, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("bookings")
    op.drop_table("work_days")
    op.drop_table("services")
