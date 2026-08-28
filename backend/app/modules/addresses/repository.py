import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.addresses.models import ShippingAddress


class ShippingAddressRepository:
    """Data access for the customer's saved shipping addresses. No business
    rules here — those live in ShippingAddressService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, address_id: uuid.UUID) -> ShippingAddress | None:
        result = await self.db.execute(
            select(ShippingAddress).where(ShippingAddress.id == address_id)
        )
        return result.scalar_one_or_none()

    async def list_for_account(self, account_id: uuid.UUID) -> list[ShippingAddress]:
        result = await self.db.execute(
            select(ShippingAddress)
            .where(ShippingAddress.account_id == account_id)
            .order_by(ShippingAddress.is_default.desc(), ShippingAddress.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_default(self, account_id: uuid.UUID) -> ShippingAddress | None:
        result = await self.db.execute(
            select(ShippingAddress).where(
                ShippingAddress.account_id == account_id,
                ShippingAddress.is_default.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        account_id: uuid.UUID,
        label: str | None,
        recipient_name: str,
        phone: str,
        country: str,
        province: str | None,
        district: str | None,
        sector: str | None,
        cell: str | None,
        village: str | None,
        address_line: str | None,
        delivery_instructions: str | None,
        latitude: float | None,
        longitude: float | None,
        is_default: bool,
    ) -> ShippingAddress:
        address = ShippingAddress(
            account_id=account_id,
            label=label,
            recipient_name=recipient_name,
            phone=phone,
            country=country,
            province=province,
            district=district,
            sector=sector,
            cell=cell,
            village=village,
            address_line=address_line,
            delivery_instructions=delivery_instructions,
            latitude=latitude,
            longitude=longitude,
            is_default=is_default,
        )
        self.db.add(address)
        await self.db.flush()
        await self.db.refresh(address)
        return address

    async def update(
        self, address: ShippingAddress, **changes
    ) -> ShippingAddress:
        for field, value in changes.items():
            if value is not None:
                setattr(address, field, value)
        await self.db.flush()
        await self.db.refresh(address)
        return address

    async def update_default(self, address: ShippingAddress, *, is_default: bool) -> None:
        address.is_default = is_default
        await self.db.flush()

    async def clear_default(self, account_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(ShippingAddress).where(
                ShippingAddress.account_id == account_id,
                ShippingAddress.is_default.is_(True),
            )
        )
        for row in result.scalars().all():
            row.is_default = False
        await self.db.flush()

    async def delete(self, address: ShippingAddress) -> None:
        await self.db.delete(address)
        await self.db.flush()
