import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.addresses.schemas import (
    ShippingAddressRequest,
    ShippingAddressResponse,
    ShippingAddressUpdateRequest,
)
from app.modules.addresses.service import ShippingAddressService
from app.modules.auth.models import Account


class ShippingAddressController:
    """Translates HTTP requests/responses to and from the address service."""

    def __init__(self, db: AsyncSession) -> None:
        self.service = ShippingAddressService(db)

    async def create(
        self, account: Account, payload: ShippingAddressRequest
    ) -> ShippingAddressResponse:
        address = await self.service.create(account.id, payload)
        return ShippingAddressResponse.model_validate(address)

    async def update(
        self,
        account: Account,
        address_id: uuid.UUID,
        payload: ShippingAddressUpdateRequest,
    ) -> ShippingAddressResponse:
        address = await self.service.update(account.id, address_id, payload)
        return ShippingAddressResponse.model_validate(address)

    async def delete(self, account: Account, address_id: uuid.UUID) -> None:
        await self.service.delete(account.id, address_id)

    async def list_for_account(self, account: Account) -> list[ShippingAddressResponse]:
        addresses = await self.service.list_for_account(account.id)
        return [ShippingAddressResponse.model_validate(a) for a in addresses]

    async def get_default(
        self, account: Account
    ) -> ShippingAddressResponse | None:
        address = await self.service.get_default(account.id)
        if address is None:
            return None
        return ShippingAddressResponse.model_validate(address)
