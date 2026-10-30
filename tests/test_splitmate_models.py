"""SplitMates schema: models, migrations and what fits in the columns."""

from types import SimpleNamespace

from alembic.config import Config
from alembic.script import ScriptDirectory

from splitmate import repo
from splitmate.models import NAME_LENGTH, Member


def test_longest_telegram_name_fits_the_column():
    # First and last names are up to 64 characters each, so the full name can be 129
    user = SimpleNamespace(full_name=f"{'A' * 64} {'B' * 64}")
    assert len(repo.member_name(user)) == NAME_LENGTH == Member.__table__.c.name.type.length


def test_migrations_have_a_single_head():
    cfg = Config()
    cfg.set_main_option("script_location", "splitmate:migrations")
    assert len(ScriptDirectory.from_config(cfg).get_heads()) == 1
