"""Data access for service requests. No business rules, and no commits: the
service owns the transaction (AGENTS.md §13)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.service_requests.service_request_model import ServiceRequest
from app.shared.responses.pagination import PaginationParams


class ServiceRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self, request_id: uuid.UUID, *, for_update: bool = False
    ) -> ServiceRequest | None:
        statement = select(ServiceRequest).where(ServiceRequest.id == request_id)
        if for_update:
            # Every answer to a request locks it first, so a buyer's cancel
            # and a provider's accept can never both win.
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def add(self, request: ServiceRequest) -> None:
        self._session.add(request)
        await self._session.flush()

    async def list_requests(
        self,
        pagination: PaginationParams,
        *,
        buyer_account_id: uuid.UUID | None = None,
        seller_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> tuple[list[ServiceRequest], int]:
        statement = select(ServiceRequest)
        if buyer_account_id is not None:
            statement = statement.where(ServiceRequest.buyer_account_id == buyer_account_id)
        if seller_id is not None:
            statement = statement.where(ServiceRequest.seller_id == seller_id)
        if status is not None:
            statement = statement.where(ServiceRequest.status == status)
        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = await self._session.scalars(
            statement.order_by(ServiceRequest.created_at.desc(), ServiceRequest.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0
