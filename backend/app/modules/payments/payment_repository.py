"""Data access for payments. No business rules, and no commits: the service
owns the transaction (AGENTS.md §13)."""

import uuid

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payments.payment_model import Payment, PaymentDestination
from app.shared.responses.pagination import PaginationParams


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Destinations ─────────────────────────────────────────────────────

    async def get_destination(self, destination_id: uuid.UUID) -> PaymentDestination | None:
        return await self._session.get(PaymentDestination, destination_id)

    async def add_destination(self, destination: PaymentDestination) -> None:
        self._session.add(destination)
        await self._session.flush()

    async def delete_destination(self, destination: PaymentDestination) -> None:
        await self._session.delete(destination)
        await self._session.flush()

    async def clear_default(self, currency: str) -> None:
        """Un-default the currency's current default, and write it at once so
        another row can become the default in the same transaction."""
        await self._session.execute(
            update(PaymentDestination)
            .where(PaymentDestination.currency == currency, PaymentDestination.is_default)
            .values(is_default=False)
        )

    async def list_active_destinations(self, currency: str) -> list[PaymentDestination]:
        """What a buyer may pay to: the default first."""
        rows = await self._session.scalars(
            select(PaymentDestination)
            .where(PaymentDestination.is_active, PaymentDestination.currency == currency)
            .order_by(
                PaymentDestination.is_default.desc(),
                PaymentDestination.provider,
                PaymentDestination.id,
            )
        )
        return list(rows)

    async def list_destinations(
        self, pagination: PaginationParams
    ) -> tuple[list[PaymentDestination], int]:
        total = await self._session.scalar(select(func.count()).select_from(PaymentDestination))
        rows = await self._session.scalars(
            select(PaymentDestination)
            .order_by(
                PaymentDestination.is_active.desc(),
                PaymentDestination.is_default.desc(),
                PaymentDestination.provider,
                PaymentDestination.id,
            )
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0

    # ── Payments ─────────────────────────────────────────────────────────

    async def get_payment(
        self, payment_id: uuid.UUID, *, for_update: bool = False
    ) -> Payment | None:
        statement = select(Payment).where(Payment.id == payment_id)
        if for_update:
            # Two approvals of the same payment are handled one at a time.
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def add_payment(self, payment: Payment) -> None:
        self._session.add(payment)
        await self._session.flush()

    async def list_for_order(self, order_id: uuid.UUID) -> list[Payment]:
        rows = await self._session.scalars(
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(Payment.created_at.desc(), Payment.id)
        )
        return list(rows)

    async def list_payments(
        self, pagination: PaginationParams, *, status: str | None, search: str | None
    ) -> tuple[list[Payment], int]:
        statement = select(Payment)
        if status is not None:
            statement = statement.where(Payment.status == status)
        if search is not None:
            # autoescape: % and _ typed by the user match literally.
            statement = statement.where(
                or_(
                    Payment.reference.icontains(search, autoescape=True),
                    Payment.order_number.icontains(search, autoescape=True),
                )
            )
        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = await self._session.scalars(
            # Oldest first: the payment that has waited longest is checked first.
            statement.order_by(Payment.created_at, Payment.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0
