import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.models import Order
from app.modules.orders.repository import OrderItemRepository
from app.modules.payments.models import Payment
from app.modules.premium.repository import (
    PremiumPlanRepository,
    SellerSubscriptionRepository,
)
from app.modules.premium.service import PremiumService
from app.modules.revenue.exceptions import RevenueAlreadyRecordedError
from app.modules.revenue.models import RevenueTransaction
from app.modules.revenue.repository import RevenueTransactionRepository
from app.modules.revenue.schemas import RevenueLine


class RevenueService:
    """Derive MUHUZE's revenue and each seller's net earning when a payment
    clears.

    Called from the payment module inside the same DB transaction as
    `Payment → paid` — so the revenue records, payment status and order
    payment status all commit together or not at all. The rate is resolved at
    *paid* time (the least-gameable moment): 7% for a premium seller, 12% for
    basic, snapshotted onto the revenue row so it stays auditable forever.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.repo = RevenueTransactionRepository(db)
        self.order_items = OrderItemRepository(db)
        self.premium = PremiumService(
            PremiumPlanRepository(db), SellerSubscriptionRepository(db)
        )

    async def breakdown_for_order(self, order_id: uuid.UUID) -> list[RevenueLine]:
        txns = await self.repo.list_for_order(order_id)
        return [_to_line(t) for t in txns]

    async def breakdown_for_seller(self, seller_id: uuid.UUID) -> list[RevenueLine]:
        txns = await self.repo.list_for_seller(seller_id)
        return [_to_line(t) for t in txns]

    async def summary_for_order(self, order_id: uuid.UUID) -> dict:
        lines = await self.breakdown_for_order(order_id)
        released = [l for l in lines if l.status == "released"]
        return {
            "total_gross": round(sum(l.amount for l in lines), 2),
            "total_commission": round(sum(l.commission_amount for l in lines), 2),
            "total_seller_earning": round(sum(l.seller_earning for l in lines), 2),
            "earnings_held": round(sum(l.seller_earning for l in lines if l.status == "held"), 2),
            "earnings_released": round(sum(l.seller_earning for l in released), 2),
        }

    async def release_for_order(self, order_id: uuid.UUID) -> int:
        """Release every still-held seller earning for an order — called when
        the buyer confirms receipt (OrderService.receive), same transaction.
        Idempotent: returns how many rows were flipped."""
        return await self.repo.release_for_order(order_id)

    async def record_for_paid_order(
        self, payment: Payment, order: Order
    ) -> list[RevenueLine]:
        """Idempotently create the revenue rows for a paid order — one per
        distinct seller, each at that seller's commission rate."""
        items = await self.order_items.list_for_order(order.id)
        gross_by_seller: dict[uuid.UUID, float] = {}
        for item in items:
            seller_id = item.seller_id
            gross_by_seller[seller_id] = round(
                gross_by_seller.get(seller_id, 0.0) + float(item.subtotal), 2
            )

        lines: list[RevenueLine] = []
        for seller_id, gross in gross_by_seller.items():
            if await self.repo.exists_for_order_seller(order.id, seller_id):
                raise RevenueAlreadyRecordedError()
            rate = await self.premium.get_commission_rate(seller_id)
            commission = round(gross * rate / 100, 2)
            earning = round(gross - commission, 2)
            txn = await self.repo.create(
                order_id=order.id,
                payment_id=payment.id,
                seller_id=seller_id,
                amount=gross,
                revenue_rate=rate,
                commission_amount=commission,
                seller_earning=earning,
                currency=order.currency,
            )
            lines.append(_to_line(txn))
        return lines

    async def list_all(self) -> list[RevenueTransaction]:
        return await self.repo.list_all()


def _to_line(txn: RevenueTransaction) -> RevenueLine:
    return RevenueLine(
        id=txn.id,
        seller_id=txn.seller_id,
        amount=float(txn.amount),
        revenue_rate=float(txn.revenue_rate),
        commission_amount=float(txn.commission_amount),
        seller_earning=float(txn.seller_earning),
        referral_eligible=bool(txn.referral_eligible),
        status=txn.status,
        released_at=txn.released_at,
    )
