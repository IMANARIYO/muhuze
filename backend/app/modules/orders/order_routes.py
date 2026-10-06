import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.modules.auth.auth_dependencies import get_current_account
from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import require_permission
from app.modules.orders.order_dependencies import get_order_service
from app.modules.orders.order_permissions import ORDER_READ, SELLER_ORDER_MANAGE
from app.modules.orders.order_schema import (
    OrderCancelRequest,
    OrderCreateRequest,
    OrderResponse,
    OrderSummaryResponse,
    OwnOrderFilters,
    ReasonRequest,
    SellerOrderFilters,
    SellerOrderResponse,
    SellerOrderSummaryResponse,
    StaffOrderFilters,
    StaffOrderResponse,
)
from app.modules.orders.order_service import OrderService
from app.modules.sellers.seller_dependencies import get_current_active_seller
from app.modules.sellers.seller_model import Seller
from app.shared.responses.api_response import APIResponse, success_response
from app.shared.responses.pagination import Page, PaginationParams

order_router = APIRouter()

ServiceDep = Annotated[OrderService, Depends(get_order_service)]
PaginationDep = Annotated[PaginationParams, Depends()]
# Every account can buy: the buyer's endpoints need a login only, and reach
# only the caller's own orders.
BuyerDep = Annotated[Account, Depends(get_current_account)]
# A seller handling their shop's orders: the permission, then an active
# seller. Ownership is checked in the service.
CanHandleDep = Annotated[Account, Depends(require_permission(SELLER_ORDER_MANAGE))]
ActiveSellerDep = Annotated[Seller, Depends(get_current_active_seller)]
StaffDep = Annotated[Account, Depends(require_permission(ORDER_READ))]

ORDERS = ["Orders"]
SHOP_ORDERS = ["Shop orders"]

# Fixed paths ("/orders/mine") are declared before "/orders/{order_id}" so
# they are never read as an id.

# ── The buyer ────────────────────────────────────────────────────────────


@order_router.post(
    "/orders",
    response_model=APIResponse[OrderResponse],
    status_code=status.HTTP_201_CREATED,
    tags=ORDERS,
)
async def place_order(
    buyer: BuyerDep, payload: OrderCreateRequest, service: ServiceDep
) -> JSONResponse:
    """Check out: send the products and quantities from the cart, and where to
    deliver. Prices and totals are worked out here, never taken from the request."""
    order = await service.place_order(buyer_account_id=buyer.id, payload=payload)
    return success_response(
        data=order,
        message="Order placed. It will be sent to the sellers once it is paid.",
        status_code=status.HTTP_201_CREATED,
    )


@order_router.get(
    "/orders/mine", response_model=APIResponse[Page[OrderSummaryResponse]], tags=ORDERS
)
async def list_my_orders(
    buyer: BuyerDep,
    pagination: PaginationDep,
    filters: Annotated[OwnOrderFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Your orders, newest first."""
    page = await service.list_own_orders(
        buyer_account_id=buyer.id, pagination=pagination, filters=filters
    )
    return success_response(data=page, message="Orders retrieved")


@order_router.get("/orders/mine/{order_id}", response_model=APIResponse[OrderResponse], tags=ORDERS)
async def get_my_order(buyer: BuyerDep, order_id: uuid.UUID, service: ServiceDep) -> JSONResponse:
    """One of your orders, with each shop's part and its status."""
    order = await service.get_own_order(buyer_account_id=buyer.id, order_id=order_id)
    return success_response(data=order, message="Order retrieved")


@order_router.post(
    "/orders/mine/{order_id}/cancel", response_model=APIResponse[OrderResponse], tags=ORDERS
)
async def cancel_my_order(
    buyer: BuyerDep, order_id: uuid.UUID, payload: OrderCancelRequest, service: ServiceDep
) -> JSONResponse:
    """Cancel the whole order. Only possible while it is unpaid."""
    order = await service.cancel_own_order(
        buyer_account_id=buyer.id, order_id=order_id, reason=payload.reason
    )
    return success_response(data=order, message="Order cancelled")


@order_router.post(
    "/orders/mine/{order_id}/seller-orders/{seller_order_id}/confirm-receipt",
    response_model=APIResponse[OrderResponse],
    tags=ORDERS,
)
async def confirm_receipt(
    buyer: BuyerDep, order_id: uuid.UUID, seller_order_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Say that one shop's part of the order has arrived."""
    order = await service.confirm_receipt(
        buyer_account_id=buyer.id, order_id=order_id, seller_order_id=seller_order_id
    )
    return success_response(data=order, message="Receipt confirmed")


# ── The seller ───────────────────────────────────────────────────────────


@order_router.get(
    "/seller-orders/mine",
    response_model=APIResponse[Page[SellerOrderSummaryResponse]],
    tags=SHOP_ORDERS,
)
async def list_my_shop_orders(
    _: CanHandleDep,
    seller: ActiveSellerDep,
    pagination: PaginationDep,
    filters: Annotated[SellerOrderFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Your shop's paid orders, newest first."""
    page = await service.list_shop_orders(
        seller_id=seller.id, pagination=pagination, filters=filters
    )
    return success_response(data=page, message="Orders retrieved")


@order_router.get(
    "/seller-orders/mine/{seller_order_id}",
    response_model=APIResponse[SellerOrderResponse],
    tags=SHOP_ORDERS,
)
async def get_my_shop_order(
    _: CanHandleDep, seller: ActiveSellerDep, seller_order_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """One order of your shop: the items, where to deliver, and what you earn."""
    order = await service.get_shop_order(seller_id=seller.id, seller_order_id=seller_order_id)
    return success_response(data=order, message="Order retrieved")


@order_router.post(
    "/seller-orders/mine/{seller_order_id}/accept",
    response_model=APIResponse[SellerOrderResponse],
    tags=SHOP_ORDERS,
)
async def accept_shop_order(
    account: CanHandleDep, seller: ActiveSellerDep, seller_order_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Agree to fulfil a pending order."""
    order = await service.accept(
        seller_id=seller.id, seller_order_id=seller_order_id, actor_id=account.id
    )
    return success_response(data=order, message="Order accepted")


@order_router.post(
    "/seller-orders/mine/{seller_order_id}/reject",
    response_model=APIResponse[SellerOrderResponse],
    tags=SHOP_ORDERS,
)
async def reject_shop_order(
    account: CanHandleDep,
    seller: ActiveSellerDep,
    seller_order_id: uuid.UUID,
    payload: ReasonRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Decline a pending order you cannot fulfil, with a reason the buyer sees."""
    order = await service.reject(
        seller_id=seller.id,
        seller_order_id=seller_order_id,
        actor_id=account.id,
        reason=payload.reason,
    )
    return success_response(data=order, message="Order rejected")


@order_router.post(
    "/seller-orders/mine/{seller_order_id}/ship",
    response_model=APIResponse[SellerOrderResponse],
    tags=SHOP_ORDERS,
)
async def ship_shop_order(
    account: CanHandleDep, seller: ActiveSellerDep, seller_order_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Mark an accepted order as sent."""
    order = await service.ship(
        seller_id=seller.id, seller_order_id=seller_order_id, actor_id=account.id
    )
    return success_response(data=order, message="Order marked as shipped")


@order_router.post(
    "/seller-orders/mine/{seller_order_id}/deliver",
    response_model=APIResponse[SellerOrderResponse],
    tags=SHOP_ORDERS,
)
async def deliver_shop_order(
    account: CanHandleDep, seller: ActiveSellerDep, seller_order_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Mark a shipped order as delivered. The buyer confirms receipt to complete it."""
    order = await service.deliver(
        seller_id=seller.id, seller_order_id=seller_order_id, actor_id=account.id
    )
    return success_response(data=order, message="Order marked as delivered")


# ── Staff ────────────────────────────────────────────────────────────────


@order_router.get("/orders", response_model=APIResponse[Page[OrderSummaryResponse]], tags=ORDERS)
async def list_all_orders(
    _: StaffDep,
    pagination: PaginationDep,
    filters: Annotated[StaffOrderFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Every order. Filter by status or buyer, or search by order number."""
    page = await service.list_all_orders(pagination, filters)
    return success_response(data=page, message="Orders retrieved")


@order_router.get("/orders/{order_id}", response_model=APIResponse[StaffOrderResponse], tags=ORDERS)
async def get_any_order(_: StaffDep, order_id: uuid.UUID, service: ServiceDep) -> JSONResponse:
    """Any order in full: every shop's part, its money split, and its history."""
    return success_response(data=await service.get_any_order(order_id), message="Order retrieved")
