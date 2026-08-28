import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import get_current_account
from app.modules.auth.models import Account
from app.modules.carts.controller import CartController
from app.modules.carts.dependencies import get_cart_controller
from app.modules.carts.schemas import (
    AddCartItemRequest,
    CartResponse,
    UpdateCartItemRequest,
)
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/carts", tags=["Carts"])


@router.get("")
async def get_cart(
    account: Account = Depends(get_current_account),
    controller: CartController = Depends(get_cart_controller),
) -> APIResponse[CartResponse]:
    """The caller's cart: lines (with current product/price display info),
    count, and gross total. A cart is a temporary customer-interaction
    mechanism — the order is the permanent financial record."""
    cart = await controller.get_cart(account)
    return success_response(data=cart, message="Cart retrieved successfully")


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_item(
    payload: AddCartItemRequest,
    account: Account = Depends(get_current_account),
    controller: CartController = Depends(get_cart_controller),
) -> APIResponse[CartResponse]:
    """Add a seller listing to the cart (bumps quantity if already present).
    Purchasable/active listings only."""
    cart = await controller.add_item(account, payload)
    return success_response(data=cart, message="Item added to cart")


@router.patch("/items/{item_id}")
async def update_quantity(
    item_id: uuid.UUID,
    payload: UpdateCartItemRequest,
    account: Account = Depends(get_current_account),
    controller: CartController = Depends(get_cart_controller),
) -> APIResponse[CartResponse]:
    """Set the quantity of a cart line."""
    cart = await controller.update_quantity(account, item_id, payload)
    return success_response(data=cart, message="Cart item updated")


@router.delete("/items/{item_id}")
async def remove_item(
    item_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    controller: CartController = Depends(get_cart_controller),
) -> APIResponse[None]:
    """Remove a line from the cart."""
    await controller.remove_item(account, item_id)
    return success_response(data=None, message="Item removed from cart")


@router.delete("")
async def clear_cart(
    account: Account = Depends(get_current_account),
    controller: CartController = Depends(get_cart_controller),
) -> APIResponse[None]:
    """Remove every line from the caller's cart."""
    await controller.clear(account)
    return success_response(data=None, message="Cart cleared")
