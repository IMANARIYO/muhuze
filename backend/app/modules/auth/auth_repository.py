"""Data access for authentication. No business rules, and no commits: the
service owns the transaction (AGENTS.md §13)."""

import uuid
from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.auth_model import (
    Account,
    PasswordResetToken,
    RefreshToken,
    VerificationCode,
)


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, account_id: uuid.UUID) -> Account | None:
        return await self._session.get(Account, account_id)

    async def get_by_email(self, email: str) -> Account | None:
        return await self._session.scalar(select(Account).where(Account.email == email))

    async def get_by_phone(self, phone: str) -> Account | None:
        return await self._session.scalar(select(Account).where(Account.phone == phone))

    async def add(self, account: Account) -> None:
        self._session.add(account)
        await self._session.flush()


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, refresh_token: RefreshToken) -> None:
        self._session.add(refresh_token)
        await self._session.flush()

    async def get_by_token_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        """Locks the row, so two requests can't rotate the same token at once."""
        return await self._session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
        )

    async def get_active(
        self, *, session_id: uuid.UUID, account_id: uuid.UUID, now: datetime
    ) -> RefreshToken | None:
        return await self._session.scalar(
            select(RefreshToken).where(
                RefreshToken.id == session_id, *self._is_active(account_id, now)
            )
        )

    async def list_active(
        self, *, account_id: uuid.UUID, now: datetime, offset: int, limit: int
    ) -> list[RefreshToken]:
        result = await self._session.scalars(
            select(RefreshToken)
            .where(*self._is_active(account_id, now))
            .order_by(RefreshToken.created_at.desc(), RefreshToken.id)
            .offset(offset)
            .limit(limit)
        )
        return list(result)

    async def count_active(self, *, account_id: uuid.UUID, now: datetime) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(RefreshToken).where(*self._is_active(account_id, now))
        )
        return total or 0

    async def revoke_all(
        self, *, account_id: uuid.UUID, now: datetime, except_id: uuid.UUID | None = None
    ) -> int:
        """Revoke every live session of the account. Returns how many were revoked."""
        statement = (
            update(RefreshToken)
            .where(RefreshToken.account_id == account_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        if except_id is not None:
            statement = statement.where(RefreshToken.id != except_id)
        result = await self._session.execute(statement)
        return result.rowcount

    @staticmethod
    def _is_active(account_id: uuid.UUID, now: datetime) -> tuple:
        return (
            RefreshToken.account_id == account_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )


class VerificationCodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, code: VerificationCode) -> None:
        self._session.add(code)
        await self._session.flush()

    async def delete_unused(self, *, account_id: uuid.UUID, purpose: str) -> None:
        await self._session.execute(
            delete(VerificationCode).where(
                VerificationCode.account_id == account_id,
                VerificationCode.purpose == purpose,
                VerificationCode.used_at.is_(None),
            )
        )

    async def get_unused_for_update(
        self, *, account_id: uuid.UUID, purpose: str, now: datetime
    ) -> VerificationCode | None:
        """The account's current unexpired code, locked so that concurrent
        guesses are counted one at a time."""
        return await self._session.scalar(
            select(VerificationCode)
            .where(
                VerificationCode.account_id == account_id,
                VerificationCode.purpose == purpose,
                VerificationCode.used_at.is_(None),
                VerificationCode.expires_at > now,
            )
            .order_by(VerificationCode.created_at.desc())
            .limit(1)
            .with_for_update()
        )


class PasswordResetTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token: PasswordResetToken) -> None:
        self._session.add(token)
        await self._session.flush()

    async def delete_unused(self, *, account_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.account_id == account_id,
                PasswordResetToken.used_at.is_(None),
            )
        )

    async def get_by_token_hash_for_update(self, token_hash: str) -> PasswordResetToken | None:
        return await self._session.scalar(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
            .with_for_update()
        )
