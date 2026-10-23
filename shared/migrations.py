from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, inspect
from sqlalchemy.ext.asyncio import AsyncEngine


def _upgrade(conn: Connection, script_location: str, baseline: tuple[str, str] | None) -> None:
    cfg = Config()
    cfg.set_main_option("script_location", script_location)
    cfg.attributes["connection"] = conn
    tables = inspect(conn).get_table_names()
    # DBs created before migrations existed: mark them as already at the baseline revision
    if baseline and "alembic_version" not in tables and baseline[1] in tables:
        command.stamp(cfg, baseline[0])
    command.upgrade(cfg, "head")


async def run_migrations(
    engine: AsyncEngine, script_location: str, baseline: tuple[str, str] | None = None
) -> None:
    """Upgrade the DB to the latest revision.
    baseline = (revision, table): if `table` exists without alembic history, stamp `revision`."""
    async with engine.begin() as conn:
        await conn.run_sync(_upgrade, script_location, baseline)
