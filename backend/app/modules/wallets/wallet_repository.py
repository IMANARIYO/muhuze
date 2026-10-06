"""Data access for revenue records and wallets. No business rules, and no
commits: the service owns the transaction (AGENTS.md §13)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.wallets.wallet_model import RevenueTransaction, Wallet, WalletTransaction
from app.shared.responses.pagination import PaginationParams


class WalletRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Revenue ──────────────────────────────────────────────────────────

    async def get_revenue_for_seller_order(
        self, seller_order_id: uuid.UUID, *, for_update: bool = False
    ) -> RevenueTransaction | None:
        statement = select(RevenueTransaction).where(
            RevenueTransaction.seller_order_id == seller_order_id
        )
        if for_update:
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def list_revenue(
        self,
        pagination: PaginationParams,
        *,
        seller_id: uuid.UUID | None,
        order_id: uuid.UUID | None,
    ) -> tuple[list[RevenueTransaction], int]:
        statement = select(RevenueTransaction)
        if seller_id is not None:
            statement = statement.where(RevenueTransaction.seller_id == seller_id)
        if order_id is not None:
            statement = statement.where(RevenueTransaction.order_id == order_id)
        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = await self._session.scalars(
            statement.order_by(RevenueTransaction.created_at.desc(), RevenueTransaction.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0

    async def summarize_revenue(self, *, seller_id: uuid.UUID | None) -> tuple:
        """(sales, gross, commission, seller amount) over sales not reversed."""
        statement = select(
            func.count(),
            func.coalesce(func.sum(RevenueTransaction.gross_amount), 0),
            func.coalesce(func.sum(RevenueTransaction.commission_amount), 0),
            func.coalesce(func.sum(RevenueTransaction.seller_amount), 0),
        ).where(RevenueTransaction.reversed_at.is_(None))
        if seller_id is not None:
            statement = statement.where(RevenueTransaction.seller_id == seller_id)
        return tuple((await self._session.execute(statement)).one())

    # ── Wallets ──────────────────────────────────────────────────────────

    async def get_wallet(self, seller_id: uuid.UUID) -> Wallet | None:
        return await self._session.scalar(select(Wallet).where(Wallet.seller_id == seller_id))

    async def lock_wallet(self, seller_id: uuid.UUID, currency: str) -> Wallet:
        """The seller's wallet, created if this is their first movement, and
        locked until the transaction ends: two movements in one wallet are
        applied one after the other, never on top of each other."""
        await self._session.execute(
            insert(Wallet)
            .values(id=uuid.uuid4(), seller_id=seller_id, currency=currency)
            .on_conflict_do_nothing(index_elements=["seller_id"])
        )
        return await self._session.scalar(
            select(Wallet)
            .where(Wallet.seller_id == seller_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    # ── Wallet transactions ──────────────────────────────────────────────

    async def has_transaction(self, revenue_transaction_id: uuid.UUID, kind: str) -> bool:
        found = await self._session.scalar(
            select(WalletTransaction.id).where(
                WalletTransaction.revenue_transaction_id == revenue_transaction_id,
                WalletTransaction.kind == kind,
            )
        )
        return found is not None

    async def add(self, row: RevenueTransaction | WalletTransaction) -> None:
        self._session.add(row)
        await self._session.flush()

    async def list_transactions(
        self, wallet_id: uuid.UUID, pagination: PaginationParams
    ) -> tuple[list[tuple[WalletTransaction, RevenueTransaction]], int]:
        """A wallet's movements, newest first, each with the sale behind it."""
        condition = WalletTransaction.wallet_id == wallet_id
        total = await self._session.scalar(
            select(func.count()).select_from(WalletTransaction).where(condition)
        )
        rows = await self._session.execute(
            select(WalletTransaction, RevenueTransaction)
            .join(
                RevenueTransaction,
                RevenueTransaction.id == WalletTransaction.revenue_transaction_id,
            )
            .where(condition)
            .order_by(WalletTransaction.created_at.desc(), WalletTransaction.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return [(row[0], row[1]) for row in rows], total or 0

    async def sum_transactions(self, wallet_id: uuid.UUID) -> tuple:
        """(Σ pending changes, Σ available changes): what the balances must be."""
        row = (
            await self._session.execute(
                select(
                    func.coalesce(func.sum(WalletTransaction.pending_change), 0),
                    func.coalesce(func.sum(WalletTransaction.available_change), 0),
                ).where(WalletTransaction.wallet_id == wallet_id)
            )
        ).one()
        return tuple(row)
