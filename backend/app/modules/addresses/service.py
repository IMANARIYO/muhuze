import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.addresses.exceptions import ShippingAddressNotFoundError
from app.modules.addresses.models import ShippingAddress
from app.modules.addresses.repository import ShippingAddressRepository
from app.modules.addresses.schemas import (
    ShippingAddressRequest,
    ShippingAddressUpdateRequest,
)


class ShippingAddressService:
    """CRUD for the customer's saved shipping addresses (the address book).

    Important: an order must never read its delivery destination directly off
    these rows — at checkout the chosen address is copied into an immutable
    `shipping_infos` snapshot owned by the order, so editing an address here
    never changes past orders (orders module owns that concern).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.repo = ShippingAddressRepository(db)

    async def create(
        self, account_id: uuid.UUID, payload: ShippingAddressRequest
    ) -> ShippingAddress:
        if payload.is_default:
            await self.repo.clear_default(account_id)
        return await self.repo.create(
            account_id=account_id,
            label=payload.label,
            recipient_name=payload.recipient_name,
            phone=payload.phone,
            country=payload.country,
            province=payload.province,
            district=payload.district,
            sector=payload.sector,
            cell=payload.cell,
            village=payload.village,
            address_line=payload.address_line,
            delivery_instructions=payload.delivery_instructions,
            latitude=payload.latitude,
            longitude=payload.longitude,
            is_default=payload.is_default,
        )

    async def update(
        self,
        account_id: uuid.UUID,
        address_id: uuid.UUID,
        payload: ShippingAddressUpdateRequest,
    ) -> ShippingAddress:
        address = await self._get_owned(account_id, address_id)
        changes = payload.model_dump(exclude_unset=True, exclude_none=True)
        if changes.get("is_default") is True:
            await self.repo.clear_default(account_id)
        return await self.repo.update(address, **changes)

    async def delete(self, account_id: uuid.UUID, address_id: uuid.UUID) -> None:
        address = await self._get_owned(account_id, address_id)
        await self.repo.delete(address)

    async def list_for_account(self, account_id: uuid.UUID) -> list[ShippingAddress]:
        return await self.repo.list_for_account(account_id)

    async def get_default(self, account_id: uuid.UUID) -> ShippingAddress | None:
        return await self.repo.get_default(account_id)

    async def _get_owned(
        self, account_id: uuid.UUID, address_id: uuid.UUID
    ) -> ShippingAddress:
        address = await self.repo.get_by_id(address_id)
        if address is None or address.account_id != account_id:
            raise ShippingAddressNotFoundError()
        return address
