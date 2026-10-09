"""Data access for payout destinations and withdrawals. No business rules,
and no commits: the service owns the transaction (AGENTS.md §13)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.withdrawals.withdrawal_model import SellerPayoutDestination, Withdrawal
from app.shared.responses.pagination import PaginationParams


class WithdrawalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Payout destinations ──────────────────────────────────────────────

    async def get_destination(
        self, seller_id: uuid.UUID, destination_id: uuid.UUID, *, for_update: bool = False
    ) -> SellerPayoutDestination | None:
        """One destination, but only the seller's own: another seller's row
        behaves like it does not exist."""
        statement = select(SellerPayoutDestination).where(
            SellerPayoutDestination.id == destination_id,
            SellerPayoutDestination.seller_id == seller_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def list_destinations(
        self, seller_id: uuid.UUID, pagination: PaginationParams
    ) -> tuple[list[SellerPayoutDestination], int]:
        statement = select(SellerPayoutDestination).where(
            SellerPayoutDestination.seller_id == seller_id
        )
        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = await self._session.scalars(
            statement.order_by(
                SellerPayoutDestination.is_active.desc(),
                SellerPayoutDestination.created_at.desc(),
                SellerPayoutDestination.id,
            )
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0

    async def destination_is_used(self, destination_id: uuid.UUID) -> bool:
        found = await self._session.scalar(
            select(Withdrawal.id).where(Withdrawal.payout_destination_id == destination_id)
        )
        return found is not None

    # ── Withdrawals ──────────────────────────────────────────────────────

    async def get_withdrawal(
        self, withdrawal_id: uuid.UUID, *, for_update: bool = False
    ) -> Withdrawal | None:
        statement = select(Withdrawal).where(Withdrawal.id == withdrawal_id)
        if for_update:
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def get_withdrawal_for_seller(
        self, seller_id: uuid.UUID, withdrawal_id: uuid.UUID, *, for_update: bool = False
    ) -> Withdrawal | None:
        """One withdrawal, but only the seller's own: another seller's row
        behaves like it does not exist."""
        statement = select(Withdrawal).where(
            Withdrawal.id == withdrawal_id, Withdrawal.seller_id == seller_id
        )
        if for_update:
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def list_for_seller(
        self, seller_id: uuid.UUID, pagination: PaginationParams
    ) -> tuple[list[Withdrawal], int]:
        statement = select(Withdrawal).where(Withdrawal.seller_id == seller_id)
        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = await self._session.scalars(
            statement.order_by(Withdrawal.created_at.desc(), Withdrawal.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0

    async def list_withdrawals(
        self,
        pagination: PaginationParams,
        *,
        status: str | None,
        seller_id: uuid.UUID | None,
    ) -> tuple[list[Withdrawal], int]:
        statement = select(Withdrawal)
        if status is not None:
            statement = statement.where(Withdrawal.status == status)
        if seller_id is not None:
            statement = statement.where(Withdrawal.seller_id == seller_id)
        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = await self._session.scalars(
            statement.order_by(Withdrawal.created_at.desc(), Withdrawal.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0

    # ── Writes ───────────────────────────────────────────────────────────

    async def add(self, row: SellerPayoutDestination | Withdrawal) -> None:
        self._session.add(row)
        await self._session.flush()

    async def delete(self, row: SellerPayoutDestination) -> None:
        await self._session.delete(row)
        await self._session.flush()
