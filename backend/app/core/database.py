import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy import DateTime, event, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import StaticPool

from app.core.config import settings


class Base(AsyncAttrs, DeclarativeBase):
    pass


class UUIDPKMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


_is_sqlite = settings.database_url.startswith("sqlite")

engine = (
    create_async_engine(
        settings.database_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    if _is_sqlite
    else create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
    )
)

if _is_sqlite:
    # SQLite defaults foreign key enforcement to off; without this,
    # ondelete="CASCADE" (used throughout auth's authorization tables)
    # silently does nothing. Only relevant for the in-memory test DB —
    # Postgres enforces FKs unconditionally.
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


def ensure_aware(value: datetime) -> datetime:
    """SQLite's DateTime(timezone=True) columns store what you give them but
    don't round-trip the tzinfo flag on read — rows written as UTC come back
    naive. Postgres always returns tz-aware values, so this is a no-op there.
    Every DateTime column in this app is written as UTC (see the *_at columns
    across auth's models), so treating a naive value as UTC on the way back
    out is correct, not a guess. Needed only for Python-level comparisons
    against a fetched value (e.g. `stored.expires_at < datetime.now(UTC)`) —
    SQL-level WHERE-clause comparisons aren't affected, since those compare
    serialized values at the database layer, not Python datetime objects.
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
