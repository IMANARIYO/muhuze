import uuid

from fastapi import APIRouter, Depends, status

from app.modules.addresses.controller import ShippingAddressController
from app.modules.addresses.dependencies import get_shipping_address_controller
from app.modules.addresses.schemas import (
    ShippingAddressRequest,
    ShippingAddressResponse,
    ShippingAddressUpdateRequest,
)
from app.modules.auth.dependencies import get_current_account
from app.modules.auth.models import Account
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.get("")
async def list_addresses(
    account: Account = Depends(get_current_account),
    controller: ShippingAddressController = Depends(get_shipping_address_controller),
) -> APIResponse[list[ShippingAddressResponse]]:
    """The caller's saved shipping addresses (the address book), default first."""
    addresses = await controller.list_for_account(account)
    return success_response(data=addresses, message="Addresses retrieved")


@router.get("/default")
async def get_default(
    account: Account = Depends(get_current_account),
    controller: ShippingAddressController = Depends(get_shipping_address_controller),
) -> APIResponse[ShippingAddressResponse | None]:
    """The caller's default address, if any."""
    address = await controller.get_default(account)
    return success_response(data=address, message="Default address retrieved")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_address(
    payload: ShippingAddressRequest,
    account: Account = Depends(get_current_account),
    controller: ShippingAddressController = Depends(get_shipping_address_controller),
) -> APIResponse[ShippingAddressResponse]:
    """Save a new shipping address for the caller."""
    address = await controller.create(account, payload)
    return success_response(data=address, message="Address created")


@router.patch("/{address_id}")
async def update_address(
    address_id: uuid.UUID,
    payload: ShippingAddressUpdateRequest,
    account: Account = Depends(get_current_account),
    controller: ShippingAddressController = Depends(get_shipping_address_controller),
) -> APIResponse[ShippingAddressResponse]:
    """Update a saved address. Note: past orders keep their frozen
    `shipping_infos` snapshot — editing a saved address never changes them."""
    address = await controller.update(account, address_id, payload)
    return success_response(data=address, message="Address updated")


@router.delete("/{address_id}")
async def delete_address(
    address_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    controller: ShippingAddressController = Depends(get_shipping_address_controller),
) -> APIResponse[None]:
    """Delete a saved address."""
    await controller.delete(account, address_id)
    return success_response(data=None, message="Address deleted")
