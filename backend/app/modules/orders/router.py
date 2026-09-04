import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import get_current_account, require_role
from app.modules.auth.models import Account
from app.modules.orders.controller import OrderController
from app.modules.orders.dependencies import get_order_controller
from app.modules.orders.schemas import (
    AdminOrderSummaryResponse,
    CheckoutRequest,
    OrderDetailResponse,
    OrderSummaryResponse,
)
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def checkout(
    payload: CheckoutRequest,
    account: Account = Depends(get_current_account),
    controller: OrderController = Depends(get_order_controller),
) -> APIResponse[OrderDetailResponse]:
    """Checkout the caller's cart into a permanent order (multi-seller
    capable). The delivery destination is snapshotted into the order's
    immutable `shipping_infos` row; the cart is cleared. Money stays gross —
    the commission split is derived at payment time, not here."""
    order = await controller.checkout(account, payload)
    return success_response(data=order, message="Order created")


@router.get("")
async def list_orders(
    account: Account = Depends(get_current_account),
    controller: OrderController = Depends(get_order_controller),
) -> APIResponse[list[OrderSummaryResponse]]:
    """The caller's orders, newest first."""
    orders = await controller.list_orders(account)
    return success_response(data=orders, message="Orders retrieved")


@router.get("/admin")
async def list_all_orders(
    admin: Account = Depends(require_role("admin")),
    controller: OrderController = Depends(get_order_controller),
) -> APIResponse[list[AdminOrderSummaryResponse]]:
    """Every order across the marketplace, newest first (admin). Includes
    orders still awaiting admin confirmation of the incoming MoMo."""
    orders = await controller.list_all_orders(admin)
    return success_response(data=orders, message="Orders retrieved")


@router.get("/{order_id}")
async def get_order(
    order_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    controller: OrderController = Depends(get_order_controller),
) -> APIResponse[OrderDetailResponse]:
    """A single order with its purchased lines, immutable delivery snapshot,
    and per-seller fulfillment status."""
    order = await controller.get_detail(account, order_id)
    return success_response(data=order, message="Order retrieved")


@router.post("/{order_id}/receive")
async def receive_order(
    order_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    controller: OrderController = Depends(get_order_controller),
) -> APIResponse[OrderDetailResponse]:
    """The buyer confirms the order was received, completing it (sets
    `completed_at`). The final step of the lifecycle after sellers ship."""
    order = await controller.receive(account, order_id)
    return success_response(data=order, message="Order received")
