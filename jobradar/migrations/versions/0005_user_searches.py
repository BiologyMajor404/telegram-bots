"""Searches in the subscriber's own words instead of a fixed list of professions

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

# The fixed professions people had picked, as searches with the words the bot used for them
OLD = {
    "video_editor": (
        "Видеомонтаж",
        [
            "видеомонтаж",
            "відеомонтаж",
            "монтажер",
            "монтаж видео",
            "монтаж відео",
            "режисер монтажу",
            "режисер(ка) монтажу",
            "режисерка монтажу",
            "відео монтаж",
            "видео монтаж",
            "video editor",
            "video editing",
            "podcast editor",
            "videoedit",
            "podcast edit",
            "відеоредактор",
            "видеоредактор",
            "reels editor",
            "short-form editor",
            "youtube editor",
            "рилсмейкер",
            "premiere pro",
            "capcut",
            "davinci",
        ],
    ),
    "motion_designer": ("Моушн-дизайн", ["motion design", "motion graphic", "моушн", "animator"]),
    "graphic_designer": (
        "Графический дизайн",
        ["graphic design", "графічний дизайн", "графический дизайн"],
    ),
    "ui_ux_designer": ("UI/UX-дизайн", ["ui/ux", "ux designer", "ui designer", "product designer"]),
    "smm": ("SMM", ["smm", "social media manager", "контент-менеджер"]),
    "copywriter": (
        "Копирайтинг",
        ["copywrit", "копірайт", "копирайт", "scriptwriter", "сценарист"],
    ),
}


def upgrade() -> None:
    searches = op.create_table(
        "user_searches",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("keywords", ARRAY(sa.String(64)), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", "label"),
    )
    rows = op.get_bind().execute(sa.text("SELECT id, professions FROM subscribers")).all()
    op.bulk_insert(
        searches,
        [
            {"user_id": user_id, "label": OLD[key][0], "keywords": OLD[key][1]}
            for user_id, professions in rows
            for key in professions or []
            if key in OLD
        ],
    )
    op.drop_column("subscribers", "professions")


def downgrade() -> None:
    op.add_column(
        "subscribers",
        sa.Column(
            "professions", ARRAY(sa.String(32)), nullable=False, server_default="{video_editor}"
        ),
    )
    op.drop_table("user_searches")
