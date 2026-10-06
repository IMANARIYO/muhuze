"""Database foundation: declarative base, column mixins, engine, and sessions.

The engine and session factory are created once in `create_app()` and kept on
`app.state`. Routes never touch a session: a feature's `*_dependencies.py`
passes the request's session to its service, and the **service** decides when
to commit (AGENTS.md §13). `get_session` never commits on its own, so anything
a service did not commit is rolled back when the request ends.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import datetime

from fastapi import Request
from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config.settings import Settings
from app.core.clock import utc_now

# Deterministic constraint names, so migrations and error handling can refer
# to them (e.g. `uq_accounts_email`).
NAMING_CONVENTION = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Every datetime column is `timestamptz`.
    type_annotation_map = {datetime: DateTime(timezone=True)}


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class CreatedAtMixin:
    """For append-only records, which are created once and never updated."""

    created_at: Mapped[datetime] = mapped_column(default=utc_now, server_default=func.now())


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        default=utc_now, onupdate=utc_now, server_default=func.now()
    )


def create_database_engine(settings: Settings) -> AsyncEngine:
    # Connections are opened lazily, on first use.
    return create_async_engine(settings.database_url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False: objects stay readable after the service commits,
    # so they can be mapped to response schemas without another query.
    return async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session
