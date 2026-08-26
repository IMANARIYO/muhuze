import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sellers.repository import SellerRepository
from app.modules.sellers.schemas import SellerResponse, SellerUpsertRequest
from app.modules.sellers.service import SellerService


class SellerController:
    """Translates HTTP requests/responses to and from the seller service."""

    def __init__(self, db: AsyncSession) -> None:
        self.service = SellerService(SellerRepository(db))

    async def get_my_seller(self, account_id: uuid.UUID) -> SellerResponse:
        seller = await self.service.get_my_seller(account_id)
        return SellerResponse.model_validate(seller)

    async def upsert_my_seller(
        self, account_id: uuid.UUID, payload: SellerUpsertRequest
    ) -> SellerResponse:
        seller = await self.service.upsert_seller(
            account_id,
            store_name=payload.store_name,
            description=payload.description,
        )
        return SellerResponse.model_validate(seller)
