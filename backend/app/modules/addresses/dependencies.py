from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.addresses.controller import ShippingAddressController


def get_shipping_address_controller(
    db: AsyncSession = Depends(get_db),
) -> ShippingAddressController:
    return ShippingAddressController(db)
