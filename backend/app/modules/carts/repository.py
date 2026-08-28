import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.carts.models import CartItem


class CartItemRepository:
    """Data access for cart items. No business rules here — those live in
    CartService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, item_id: uuid.UUID) -> CartItem | None:
        result = await self.db.execute(
            select(CartItem).where(CartItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_for_account_and_listing(
        self, account_id: uuid.UUID, listing_id: uuid.UUID
    ) -> CartItem | None:
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.account_id == account_id,
                CartItem.listing_id == listing_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_account(self, account_id: uuid.UUID) -> list[CartItem]:
        result = await self.db.execute(
            select(CartItem)
            .where(CartItem.account_id == account_id)
            .order_by(CartItem.created_at.asc())
        )
        return list(result.scalars().all())

    async def create(
        self, *, account_id: uuid.UUID, listing_id: uuid.UUID, quantity: int
    ) -> CartItem:
        item = CartItem(
            account_id=account_id, listing_id=listing_id, quantity=quantity
        )
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update_quantity(self, item: CartItem, *, quantity: int) -> CartItem:
        item.quantity = quantity
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item: CartItem) -> None:
        await self.db.delete(item)
        await self.db.flush()

    async def clear_for_account(self, account_id: uuid.UUID) -> None:
        await self.db.execute(
            delete(CartItem).where(CartItem.account_id == account_id)
        )
        await self.db.flush()
