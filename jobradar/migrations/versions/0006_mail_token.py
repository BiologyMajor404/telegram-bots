"""Personal addresses for job alert emails

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
    op.add_column("subscribers", sa.Column("mail_token", sa.String(16)))
    op.create_unique_constraint("subscribers_mail_token_key", "subscribers", ["mail_token"])


def downgrade() -> None:
    op.drop_constraint("subscribers_mail_token_key", "subscribers")
    op.drop_column("subscribers", "mail_token")
