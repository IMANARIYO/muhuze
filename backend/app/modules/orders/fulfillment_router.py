import uuid

from fastapi import APIRouter, Depends, status

from app.modules.orders.dependencies import get_fulfillment_controller
from app.modules.orders.fulfillment_controller import FulfillmentController
from app.modules.orders.fulfillment_schemas import (
    RejectSellerOrderRequest,
    SellerOrderResponse,
    ShipSellerOrderRequest,
)
from app.modules.sellers.dependencies import get_current_seller
from app.modules.sellers.models import Seller
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/orders/seller", tags=["Seller Fulfillment"])


@router.get("")
async def list_my_orders(
    seller: Seller = Depends(get_current_seller),
    controller: FulfillmentController = Depends(get_fulfillment_controller),
) -> APIResponse[list[SellerOrderResponse]]:
    """The caller's fulfillment slices across all their orders, newest first."""
    rows = await controller.list_my(seller)
    return success_response(data=rows, message="Seller orders retrieved")


@router.post("/{seller_order_id}/accept")
async def accept_order(
    seller_order_id: uuid.UUID,
    seller: Seller = Depends(get_current_seller),
    controller: FulfillmentController = Depends(get_fulfillment_controller),
) -> APIResponse[SellerOrderResponse]:
    """Accept the order slice (pending -> accepted)."""
    row = await controller.accept(seller, seller_order_id)
    return success_response(data=row, message="Seller order accepted")


@router.post("/{seller_order_id}/reject")
async def reject_order(
    seller_order_id: uuid.UUID,
    payload: RejectSellerOrderRequest,
    seller: Seller = Depends(get_current_seller),
    controller: FulfillmentController = Depends(get_fulfillment_controller),
) -> APIResponse[SellerOrderResponse]:
    """Reject the order slice with a reason (pending -> rejected)."""
    row = await controller.reject(seller, seller_order_id, payload.reason)
    return success_response(data=row, message="Seller order rejected")


@router.post("/{seller_order_id}/ship")
async def ship_order(
    seller_order_id: uuid.UUID,
    payload: ShipSellerOrderRequest,
    seller: Seller = Depends(get_current_seller),
    controller: FulfillmentController = Depends(get_fulfillment_controller),
) -> APIResponse[SellerOrderResponse]:
    """Ship the slice: creates a shipment and moves it to `shipped`."""
    row = await controller.ship(
        seller,
        seller_order_id,
        carrier=payload.carrier,
        tracking_number=payload.tracking_number,
        notes=payload.notes,
    )
    return success_response(data=row, message="Seller order shipped")


@router.post("/shipments/{shipment_id}/deliver", status_code=status.HTTP_200_OK)
async def deliver_shipment(
    shipment_id: uuid.UUID,
    seller: Seller = Depends(get_current_seller),
    controller: FulfillmentController = Depends(get_fulfillment_controller),
) -> APIResponse[SellerOrderResponse]:
    """Confirm delivery of a shipment the caller owns (shipped -> delivered)."""
    row = await controller.deliver(seller, shipment_id)
    return success_response(data=row, message="Shipment delivered")
