import uuid
from datetime import datetime, UTC

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.revenue.models import RevenueTransaction
from app.modules.revenue.schemas import RevenueLine


class RevenueTransactionRepository:
    """Data access for revenue transactions. No business rules here — the
    commission math and idempotency live in RevenueService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_order(self, order_id: uuid.UUID) -> list[RevenueTransaction]:
        result = await self.db.execute(
            select(RevenueTransaction)
            .where(RevenueTransaction.order_id == order_id)
            .order_by(RevenueTransaction.seller_id)
        )
        return list(result.scalars().all())

    async def list_for_seller(self, seller_id: uuid.UUID) -> list[RevenueTransaction]:
        result = await self.db.execute(
            select(RevenueTransaction)
            .where(RevenueTransaction.seller_id == seller_id)
            .order_by(RevenueTransaction.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_order_seller(
        self, order_id: uuid.UUID, seller_id: uuid.UUID
    ) -> RevenueTransaction | None:
        result = await self.db.execute(
            select(RevenueTransaction).where(
                RevenueTransaction.order_id == order_id,
                RevenueTransaction.seller_id == seller_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[RevenueTransaction]:
        result = await self.db.execute(
            select(RevenueTransaction).order_by(RevenueTransaction.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        order_id: uuid.UUID,
        payment_id: uuid.UUID,
        seller_id: uuid.UUID,
        amount: float,
        revenue_rate: float,
        commission_amount: float,
        seller_earning: float,
        currency: str,
        referral_eligible: bool = False,
    ) -> RevenueTransaction:
        txn = RevenueTransaction(
            order_id=order_id,
            payment_id=payment_id,
            seller_id=seller_id,
            amount=amount,
            revenue_rate=revenue_rate,
            commission_amount=commission_amount,
            seller_earning=seller_earning,
            currency=currency,
            referral_eligible=referral_eligible,
        )
        self.db.add(txn)
        await self.db.flush()
        await self.db.refresh(txn)
        return txn

    async def exists_for_order_seller(
        self, order_id: uuid.UUID, seller_id: uuid.UUID
    ) -> bool:
        result = await self.db.execute(
            select(RevenueTransaction.id).where(
                RevenueTransaction.order_id == order_id,
                RevenueTransaction.seller_id == seller_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def list_held_for_order(self, order_id: uuid.UUID) -> list[RevenueTransaction]:
        result = await self.db.execute(
            select(RevenueTransaction).where(
                RevenueTransaction.order_id == order_id,
                RevenueTransaction.status == "held",
            )
        )
        return list(result.scalars().all())

    async def release_for_order(
        self, order_id: uuid.UUID, released_at: datetime | None = None
    ) -> int:
        """Release every still-held earning for an order. Returns how many
        rows were flipped. Idempotent: already-released rows are untouched."""
        now = released_at or datetime.now(UTC)
        result = await self.db.execute(
            update(RevenueTransaction)
            .where(
                RevenueTransaction.order_id == order_id,
                RevenueTransaction.status == "held",
            )
            .values(status="released", released_at=now)
        )
        await self.db.flush()
        return result.rowcount or 0


def to_revenue_line(txn: RevenueTransaction) -> RevenueLine:
    return RevenueLine(
        id=txn.id,
        order_id=txn.order_id,
        seller_id=txn.seller_id,
        amount=float(txn.amount),
        revenue_rate=float(txn.revenue_rate),
        commission_amount=float(txn.commission_amount),
        seller_earning=float(txn.seller_earning),
        referral_eligible=bool(txn.referral_eligible),
        status=txn.status,
        released_at=txn.released_at,
    )
