"""Per-subscriber filters: professions, remote, schedule, languages, regions, country

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

# Existing subscribers keep the conditions the bot was built with
COLUMNS = [
    sa.Column("professions", ARRAY(sa.String(32)), nullable=False, server_default="{video_editor}"),
    sa.Column("remote_only", sa.Boolean, nullable=False, server_default=sa.true()),
    sa.Column("flexible_only", sa.Boolean, nullable=False, server_default=sa.true()),
    sa.Column("languages", ARRAY(sa.String(8)), nullable=False, server_default="{en,uk,ru}"),
    sa.Column("regions", ARRAY(sa.String(16)), nullable=False, server_default="{us,eu,ua}"),
    sa.Column("country", sa.String(8), nullable=False, server_default="UA"),
]


def upgrade() -> None:
    for column in COLUMNS:
        op.add_column("subscribers", column)


def downgrade() -> None:
    for column in reversed(COLUMNS):
        op.drop_column("subscribers", column.name)
