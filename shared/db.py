from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shared.migrations import run_migrations


async def init_db(
    url: str, migrations: str, baseline: tuple[str, str] | None = None
) -> tuple[AsyncEngine, async_sessionmaker]:
    """Create the engine, apply migrations and return a session factory."""
    engine = create_async_engine(url, pool_pre_ping=True)
    await run_migrations(engine, migrations, baseline)
    return engine, async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
