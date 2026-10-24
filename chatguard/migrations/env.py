"""Alembic env: runs on the connection passed in by shared.migrations.run_migrations."""

from alembic import context

from chatguard.models import Base

context.configure(
    connection=context.config.attributes["connection"],
    target_metadata=Base.metadata,
)
with context.begin_transaction():
    context.run_migrations()
