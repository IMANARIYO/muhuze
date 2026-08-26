import uuid

from app.modules.sellers.exceptions import (
    SellerNotFoundError,
    StoreNameAlreadyTakenError,
)
from app.modules.sellers.models import Seller
from app.modules.sellers.repository import SellerRepository


class SellerService:
    """Business rules for sellers."""

    def __init__(self, repository: SellerRepository) -> None:
        self.repository = repository

    async def get_my_seller(self, account_id: uuid.UUID) -> Seller:
        seller = await self.repository.get_by_account_id(account_id)
        if seller is None:
            raise SellerNotFoundError()
        return seller

    async def upsert_seller(
        self, account_id: uuid.UUID, *, store_name: str, description: str | None
    ) -> Seller:
        existing = await self.repository.get_by_account_id(account_id)

        holder = await self.repository.get_by_store_name(store_name)
        if holder is not None and holder.account_id != account_id:
            raise StoreNameAlreadyTakenError()

        if existing is None:
            return await self.repository.create(
                account_id=account_id, store_name=store_name, description=description
            )
        return await self.repository.update(
            existing, store_name=store_name, description=description
        )
