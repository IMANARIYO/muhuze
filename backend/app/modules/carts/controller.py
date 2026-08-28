import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Account
from app.modules.carts.schemas import (
    AddCartItemRequest,
    CartResponse,
    UpdateCartItemRequest,
)
from app.modules.carts.service import CartService


class CartController:
    """Translates HTTP requests/responses to and from the cart service.
    Every mutation responds with the refreshed `CartResponse`, so the frontend
    always has the current cart state (and gross total) after any change."""

    def __init__(self, db: AsyncSession) -> None:
        self.service = CartService(db)

    async def add_item(
        self, account: Account, payload: AddCartItemRequest
    ) -> CartResponse:
        await self.service.add_item(account.id, payload)
        return await self.service.get_cart(account.id)

    async def update_quantity(
        self, account: Account, item_id: uuid.UUID, payload: UpdateCartItemRequest
    ) -> CartResponse:
        await self.service.update_quantity(account.id, item_id, payload)
        return await self.service.get_cart(account.id)

    async def remove_item(self, account: Account, item_id: uuid.UUID) -> None:
        await self.service.remove_item(account.id, item_id)

    async def clear(self, account: Account) -> None:
        await self.service.clear(account.id)

    async def get_cart(self, account: Account) -> CartResponse:
        return await self.service.get_cart(account.id)
