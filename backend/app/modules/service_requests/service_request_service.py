"""Service requests: how a buyer gets a service (README §7.5, §20 X2).
Rules are documented in docs/features/019_service_requests.md.

    requested ──► accepted   (the provider agrees → an order is created to pay)
        │    └──► declined   (the provider says no, with a reason)
        └──────► cancelled   (the buyer withdraws it before an answer)

Nothing is paid until the provider accepts, so a busy provider never causes
a refund. Acceptance hands over to orders: from then on the order is paid,
done, confirmed, and settled like any other, and this request only points
at it. The price is the one the buyer saw when asking.

Every public method is one unit of work and commits it.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utc_now
from app.core.logging import get_logger
from app.modules.orders.order_schema import DeliveryRequest, DeliveryResponse
from app.modules.orders.order_service import OrderService
from app.modules.products.product_constants import ProductKind
from app.modules.products.product_exceptions import ProductNotFoundError
from app.modules.products.product_schema import PublicProductResponse
from app.modules.products.product_service import ProductService
from app.modules.sellers.seller_service import SellerService
from app.modules.service_requests.service_request_constants import ServiceRequestStatus
from app.modules.service_requests.service_request_exceptions import (
    NotAServiceError,
    OwnServiceRequestError,
    ScheduledTimeInPastError,
    ServiceNoLongerOfferedError,
    ServiceNotFoundError,
    ServiceRequestNotFoundError,
    ServiceRequestStatusConflictError,
)
from app.modules.service_requests.service_request_model import ServiceRequest
from app.modules.service_requests.service_request_repository import ServiceRequestRepository
from app.modules.service_requests.service_request_schema import (
    ServiceRequestCreateRequest,
    ServiceRequestFilters,
    ServiceRequestResponse,
    StaffServiceRequestFilters,
)
from app.shared.responses.pagination import Page, PaginationParams

logger = get_logger(__name__)

R = ServiceRequestStatus


class ServiceRequestService:
    def __init__(
        self,
        session: AsyncSession,
        product_service: ProductService,
        order_service: OrderService,
        seller_service: SellerService,
    ) -> None:
        self._session = session
        self._products = product_service
        self._orders = order_service
        self._sellers = seller_service
        self._repository = ServiceRequestRepository(session)

    # ── The buyer ────────────────────────────────────────────────────────

    async def create_request(
        self, *, buyer_account_id: uuid.UUID, payload: ServiceRequestCreateRequest
    ) -> ServiceRequestResponse:
        """Ask a provider for a service at a time and place. Nothing is paid
        yet: the buyer pays only once the provider accepts."""
        service = await self._service_on_offer(payload.service_id)
        if service.kind != ProductKind.SERVICE:
            raise NotAServiceError()
        if await self._sellers.find_seller_id(buyer_account_id) == service.seller_id:
            raise OwnServiceRequestError()
        if payload.scheduled_for <= utc_now():
            raise ScheduledTimeInPastError()

        location = payload.location
        request = ServiceRequest(
            buyer_account_id=buyer_account_id,
            seller_id=service.seller_id,
            product_id=service.id,
            service_name=service.name,
            seller_name=service.shop.name,
            unit_price=service.price,
            currency=service.currency,
            scheduled_for=payload.scheduled_for,
            contact_name=location.recipient_name,
            contact_phone=location.recipient_phone,
            province=location.province,
            district=location.district,
            sector=location.sector,
            address=location.address or None,
            note=payload.note or None,
            status=R.REQUESTED.value,
        )
        await self._repository.add(request)
        await self._session.commit()
        logger.info(
            "service requested",
            extra={"service_request_id": str(request.id), "seller_id": str(request.seller_id)},
        )
        return await self._response(request)

    async def list_own_requests(
        self,
        *,
        buyer_account_id: uuid.UUID,
        pagination: PaginationParams,
        filters: ServiceRequestFilters,
    ) -> Page[ServiceRequestResponse]:
        rows, total = await self._repository.list_requests(
            pagination,
            buyer_account_id=buyer_account_id,
            status=filters.status.value if filters.status else None,
        )
        return await self._page(rows, total, pagination)

    async def get_own_request(
        self, *, buyer_account_id: uuid.UUID, request_id: uuid.UUID
    ) -> ServiceRequestResponse:
        return await self._response(await self._own(buyer_account_id, request_id))

    async def cancel_own_request(
        self, *, buyer_account_id: uuid.UUID, request_id: uuid.UUID, reason: str | None
    ) -> ServiceRequestResponse:
        """The buyer withdraws a request the provider has not answered yet.
        Once accepted, the buyer cancels the unpaid ORDER instead."""
        request = await self._own(buyer_account_id, request_id, for_update=True)
        self._require_open(request, "Only a request still waiting for an answer can be cancelled")
        request.status = R.CANCELLED.value
        request.status_reason = reason
        request.cancelled_at = utc_now()
        await self._session.commit()
        logger.info("service request cancelled", extra={"service_request_id": str(request.id)})
        return await self._response(request)

    # ── The provider ─────────────────────────────────────────────────────

    async def list_incoming_requests(
        self, *, seller_id: uuid.UUID, pagination: PaginationParams, filters: ServiceRequestFilters
    ) -> Page[ServiceRequestResponse]:
        rows, total = await self._repository.list_requests(
            pagination,
            seller_id=seller_id,
            status=filters.status.value if filters.status else None,
        )
        return await self._page(rows, total, pagination)

    async def get_incoming_request(
        self, *, seller_id: uuid.UUID, request_id: uuid.UUID
    ) -> ServiceRequestResponse:
        return await self._response(await self._incoming(seller_id, request_id))

    async def accept(
        self, *, seller_id: uuid.UUID, request_id: uuid.UUID, actor_id: uuid.UUID
    ) -> ServiceRequestResponse:
        """The provider agrees. The order the buyer pays is created in the
        same transaction, at the price the buyer saw when asking."""
        request = await self._incoming(seller_id, request_id, for_update=True)
        self._require_open(request, "Only a request still waiting for an answer can be accepted")
        if request.scheduled_for <= utc_now():
            raise ScheduledTimeInPastError(
                "The requested time has passed. The buyer can send a new request."
            )
        try:
            # The listing must still be on offer: not archived, not hidden by staff.
            service = await self._service_on_offer(request.product_id)
        except ServiceNotFoundError as exc:
            raise ServiceNoLongerOfferedError() from exc

        order = await self._orders.create_service_order(
            buyer_account_id=request.buyer_account_id,
            service=service,
            unit_price=request.unit_price,
            currency=request.currency,
            scheduled_for=request.scheduled_for,
            location=DeliveryRequest(
                recipient_name=request.contact_name,
                recipient_phone=request.contact_phone,
                province=request.province,
                district=request.district,
                sector=request.sector,
                address=request.address,
            ),
            note=request.note,
            actor_id=actor_id,
        )
        request.status = R.ACCEPTED.value
        request.order_id = order.id
        self._answered(request, actor_id)
        await self._session.commit()
        logger.info(
            "service request accepted",
            extra={"service_request_id": str(request.id), "order_id": str(order.id)},
        )
        return await self._response(request)

    async def decline(
        self, *, seller_id: uuid.UUID, request_id: uuid.UUID, actor_id: uuid.UUID, reason: str
    ) -> ServiceRequestResponse:
        """The provider says no, with a reason the buyer sees. Nothing was paid."""
        request = await self._incoming(seller_id, request_id, for_update=True)
        self._require_open(request, "Only a request still waiting for an answer can be declined")
        request.status = R.DECLINED.value
        request.status_reason = reason
        self._answered(request, actor_id)
        await self._session.commit()
        logger.info("service request declined", extra={"service_request_id": str(request.id)})
        return await self._response(request)

    # ── Staff ────────────────────────────────────────────────────────────

    async def list_all_requests(
        self, pagination: PaginationParams, filters: StaffServiceRequestFilters
    ) -> Page[ServiceRequestResponse]:
        rows, total = await self._repository.list_requests(
            pagination,
            buyer_account_id=filters.buyer_account_id,
            seller_id=filters.seller_id,
            status=filters.status.value if filters.status else None,
        )
        return await self._page(rows, total, pagination)

    async def get_any_request(self, request_id: uuid.UUID) -> ServiceRequestResponse:
        request = await self._repository.get(request_id)
        if request is None:
            raise ServiceRequestNotFoundError()
        return await self._response(request)

    # ── Loading, ownership, and status ───────────────────────────────────

    async def _own(
        self, buyer_account_id: uuid.UUID, request_id: uuid.UUID, *, for_update: bool = False
    ) -> ServiceRequest:
        """The buyer's ownership check: another buyer's request is "not found"."""
        request = await self._repository.get(request_id, for_update=for_update)
        if request is None or request.buyer_account_id != buyer_account_id:
            raise ServiceRequestNotFoundError()
        return request

    async def _incoming(
        self, seller_id: uuid.UUID, request_id: uuid.UUID, *, for_update: bool = False
    ) -> ServiceRequest:
        """The provider's ownership check: another shop's request is "not found"."""
        request = await self._repository.get(request_id, for_update=for_update)
        if request is None or request.seller_id != seller_id:
            raise ServiceRequestNotFoundError()
        return request

    async def _service_on_offer(self, product_id: uuid.UUID) -> PublicProductResponse:
        """The listing as a buyer can see it right now, or "not found"."""
        try:
            return await self._products.get_public_product(product_id)
        except ProductNotFoundError as exc:
            raise ServiceNotFoundError() from exc

    @staticmethod
    def _require_open(request: ServiceRequest, message: str) -> None:
        if request.status != R.REQUESTED:
            raise ServiceRequestStatusConflictError(message)

    @staticmethod
    def _answered(request: ServiceRequest, actor_id: uuid.UUID) -> None:
        request.responded_by_account_id = actor_id
        request.responded_at = utc_now()

    # ── Responses ────────────────────────────────────────────────────────

    async def _response(self, request: ServiceRequest) -> ServiceRequestResponse:
        return (await self._responses([request]))[0]

    async def _responses(self, requests: list[ServiceRequest]) -> list[ServiceRequestResponse]:
        """One extra query for the orders of the whole page."""
        orders = await self._orders.get_order_summaries(
            [request.order_id for request in requests if request.order_id is not None]
        )
        return [
            ServiceRequestResponse(
                id=request.id,
                status=request.status,
                status_reason=request.status_reason,
                service_id=request.product_id,
                service_name=request.service_name,
                seller_id=request.seller_id,
                seller_name=request.seller_name,
                buyer_account_id=request.buyer_account_id,
                unit_price=request.unit_price,
                currency=request.currency,
                scheduled_for=request.scheduled_for,
                location=DeliveryResponse(
                    recipient_name=request.contact_name,
                    recipient_phone=request.contact_phone,
                    province=request.province,
                    district=request.district,
                    sector=request.sector,
                    address=request.address,
                    note=request.note,
                ),
                responded_at=request.responded_at,
                cancelled_at=request.cancelled_at,
                created_at=request.created_at,
                order=orders.get(request.order_id) if request.order_id else None,
            )
            for request in requests
        ]

    async def _page(
        self, requests: list[ServiceRequest], total: int, pagination: PaginationParams
    ) -> Page[ServiceRequestResponse]:
        return Page[ServiceRequestResponse].build(
            await self._responses(requests), total, pagination
        )
