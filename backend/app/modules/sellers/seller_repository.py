"""Data access for sellers. No business rules, and no commits: the service
owns the transaction (AGENTS.md §13)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sellers.seller_model import Seller, SellerDocument, SellerStatusHistory
from app.shared.responses.pagination import PaginationParams

# The sort keys a client may ask for, mapped to real columns. Nothing else
# from the request ever reaches ORDER BY.
SORT_COLUMNS = {
    "created_at": Seller.created_at,
    "submitted_at": Seller.submitted_at,
    "business_name": func.lower(Seller.business_name),
}


class SellerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Sellers ──────────────────────────────────────────────────────────

    async def get(self, seller_id: uuid.UUID, *, for_update: bool = False) -> Seller | None:
        return await self._one(select(Seller).where(Seller.id == seller_id), for_update)

    async def get_by_account(
        self, account_id: uuid.UUID, *, for_update: bool = False
    ) -> Seller | None:
        return await self._one(select(Seller).where(Seller.account_id == account_id), for_update)

    async def business_name_exists(
        self, business_name: str, *, except_seller_id: uuid.UUID | None = None
    ) -> bool:
        statement = select(Seller.id).where(
            func.lower(Seller.business_name) == business_name.lower()
        )
        if except_seller_id is not None:
            statement = statement.where(Seller.id != except_seller_id)
        return await self._session.scalar(statement) is not None

    async def add(self, seller: Seller) -> None:
        self._session.add(seller)
        await self._session.flush()

    async def list_sellers(
        self,
        pagination: PaginationParams,
        *,
        status: str | None,
        search: str | None,
        sort: str,
    ) -> tuple[list[Seller], int]:
        statement = select(Seller)
        if status is not None:
            statement = statement.where(Seller.status == status)
        if search is not None:
            # autoescape: % and _ typed by the user match literally.
            statement = statement.where(Seller.business_name.icontains(search, autoescape=True))

        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        column = SORT_COLUMNS[sort.removeprefix("-")]
        order = column.desc().nulls_last() if sort.startswith("-") else column.asc().nulls_last()
        rows = await self._session.scalars(
            # The id makes the order stable when two rows share the sort value.
            statement.order_by(order, Seller.id).offset(pagination.offset).limit(pagination.limit)
        )
        return list(rows), total or 0

    # ── Documents ────────────────────────────────────────────────────────

    async def list_documents(self, seller_id: uuid.UUID) -> list[SellerDocument]:
        rows = await self._session.scalars(
            select(SellerDocument)
            .where(SellerDocument.seller_id == seller_id)
            .order_by(SellerDocument.document_type)
        )
        return list(rows)

    async def get_document(self, seller_id: uuid.UUID, document_type: str) -> SellerDocument | None:
        return await self._session.scalar(
            select(SellerDocument).where(
                SellerDocument.seller_id == seller_id,
                SellerDocument.document_type == document_type,
            )
        )

    async def add_document(self, document: SellerDocument) -> None:
        self._session.add(document)
        await self._session.flush()

    async def delete_document(self, document: SellerDocument) -> None:
        await self._session.delete(document)
        await self._session.flush()

    # ── Status history ───────────────────────────────────────────────────

    async def add_history(self, entry: SellerStatusHistory) -> None:
        self._session.add(entry)
        await self._session.flush()

    async def list_history(
        self, seller_id: uuid.UUID, pagination: PaginationParams
    ) -> tuple[list[SellerStatusHistory], int]:
        condition = SellerStatusHistory.seller_id == seller_id
        total = await self._session.scalar(
            select(func.count()).select_from(SellerStatusHistory).where(condition)
        )
        rows = await self._session.scalars(
            select(SellerStatusHistory)
            .where(condition)
            .order_by(SellerStatusHistory.created_at.desc(), SellerStatusHistory.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0

    async def _one(self, statement, for_update: bool) -> Seller | None:
        if for_update:
            # Serializes concurrent status changes of the same seller.
            statement = statement.with_for_update()
        return await self._session.scalar(statement)
