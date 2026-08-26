import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sellers.models import Seller


class SellerRepository:
    """Data access for sellers. No business rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_account_id(self, account_id: uuid.UUID) -> Seller | None:
        result = await self.db.execute(
            select(Seller).where(Seller.account_id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_by_store_name(self, store_name: str) -> Seller | None:
        result = await self.db.execute(
            select(Seller).where(Seller.store_name == store_name)
        )
        return result.scalar_one_or_none()

    async def create(
        self, *, account_id: uuid.UUID, store_name: str, description: str | None
    ) -> Seller:
        seller = Seller(
            account_id=account_id, store_name=store_name, description=description
        )
        self.db.add(seller)
        await self.db.flush()
        await self.db.refresh(seller)
        return seller

    async def update(
        self, seller: Seller, *, store_name: str, description: str | None
    ) -> Seller:
        seller.store_name = store_name
        seller.description = description
        await self.db.flush()
        await self.db.refresh(seller)
        return seller
