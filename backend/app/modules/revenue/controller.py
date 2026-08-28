import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.revenue.schemas import (
    RevenueLine,
    RevenueTransactionResponse,
)
from app.modules.revenue.service import RevenueService


class RevenueController:
    """Translates HTTP requests/responses to and from the revenue service."""

    def __init__(self, db: AsyncSession) -> None:
        self.service = RevenueService(db)

    async def order_breakdown(self, order_id: uuid.UUID) -> list[RevenueLine]:
        return await self.service.breakdown_for_order(order_id)

    async def seller_breakdown(self, seller_id: uuid.UUID) -> list[RevenueLine]:
        return await self.service.breakdown_for_seller(seller_id)

    async def order_summary(self, order_id: uuid.UUID) -> dict:
        return await self.service.summary_for_order(order_id)

    async def list_all(self) -> list[RevenueTransactionResponse]:
        txns = await self.service.list_all()
        return [RevenueTransactionResponse.model_validate(t) for t in txns]
