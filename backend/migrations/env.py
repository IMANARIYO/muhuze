import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.settings import get_settings
from app.core import model_registry  # noqa: F401 - registers every model on Base.metadata
from app.core.database import Base

config = context.config

# The test suite runs migrations programmatically and turns this off so
# Alembic doesn't reconfigure logging underneath pytest.
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def get_database_url() -> str:
    # A caller (the test suite) may pass a URL explicitly; otherwise the
    # application's own DATABASE_URL is used.
    return config.attributes.get("database_url") or get_settings().database_url


def run_migrations_offline() -> None:
    """Emit SQL without connecting: `alembic upgrade head --sql`."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(get_database_url(), poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
