import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.modules.auth.models import Account
from app.modules.auth.repository import AccountRepository, AuthorizationRepository
from app.modules.sellers.models import SellerDocument
from app.modules.sellers.repository import SellerDocumentRepository, SellerRepository
from app.modules.sellers.schemas import (
    RejectSellerRequest,
    SellerDocumentResponse,
    SellerRegistrationRequest,
    SellerResponse,
    SellerUpdateRequest,
    SuspendSellerRequest,
)
from app.modules.sellers.service import SellerDocumentService, SellerService


class SellerController:
    """Translates HTTP requests/responses to and from the seller services."""

    def __init__(self, db: AsyncSession) -> None:
        sellers = SellerRepository(db)
        documents = SellerDocumentRepository(db)
        self.sellers = SellerService(
            sellers, documents, AccountRepository(db), AuthorizationRepository(db)
        )
        self.documents = SellerDocumentService(sellers, documents)

    # --- self-service -------------------------------------------------

    async def register(
        self, account: Account, payload: SellerRegistrationRequest
    ) -> SellerResponse:
        seller = await self.sellers.register(
            account,
            business_name=payload.business_name,
            business_description=payload.business_description,
        )
        return SellerResponse.model_validate(seller)

    async def get_my_seller(self, account: Account) -> SellerResponse:
        seller = await self.sellers.get_my_seller(account.id)
        return SellerResponse.model_validate(seller)

    async def update_my_profile(
        self, account: Account, payload: SellerUpdateRequest
    ) -> SellerResponse:
        seller = await self.sellers.update_profile(
            account.id,
            business_name=payload.business_name,
            business_description=payload.business_description,
        )
        return SellerResponse.model_validate(seller)

    async def submit_for_review(self, account: Account) -> SellerResponse:
        seller = await self.sellers.submit_for_review(account)
        return SellerResponse.model_validate(seller)

    async def deactivate(self, account: Account) -> SellerResponse:
        seller = await self.sellers.deactivate(account)
        return SellerResponse.model_validate(seller)

    async def upload_my_document(
        self, account: Account, *, document_type: str, file: UploadFile
    ) -> SellerDocumentResponse:
        document = await self.documents.upload_document(
            account.id, document_type=document_type, file=file
        )
        return await self._to_document_response(document)

    async def list_my_documents(self, account: Account) -> list[SellerDocumentResponse]:
        documents = await self.documents.list_documents(account.id)
        return [await self._to_document_response(document) for document in documents]

    async def delete_my_document(
        self, account: Account, document_id: uuid.UUID
    ) -> None:
        await self.documents.delete_document(account.id, document_id)

    # --- admin ----------------------------------------------------------

    async def list_sellers(self, *, status: str | None) -> list[SellerResponse]:
        sellers = await self.sellers.list_sellers(status=status)
        return [SellerResponse.model_validate(seller) for seller in sellers]

    async def get_seller(self, seller_id: uuid.UUID) -> SellerResponse:
        seller = await self.sellers.get_seller_by_id(seller_id)
        return SellerResponse.model_validate(seller)

    async def list_seller_documents(
        self, seller_id: uuid.UUID
    ) -> list[SellerDocumentResponse]:
        documents = await self.documents.list_documents_for_seller(seller_id)
        return [await self._to_document_response(document) for document in documents]

    async def approve(self, seller_id: uuid.UUID, admin: Account) -> SellerResponse:
        seller = await self.sellers.approve(seller_id, admin_account_id=admin.id)
        return SellerResponse.model_validate(seller)

    async def reject(
        self, seller_id: uuid.UUID, admin: Account, payload: RejectSellerRequest
    ) -> SellerResponse:
        seller = await self.sellers.reject(
            seller_id, admin_account_id=admin.id, reason=payload.reason
        )
        return SellerResponse.model_validate(seller)

    async def suspend(
        self, seller_id: uuid.UUID, payload: SuspendSellerRequest
    ) -> SellerResponse:
        seller = await self.sellers.suspend(seller_id, reason=payload.reason)
        return SellerResponse.model_validate(seller)

    async def reactivate(self, seller_id: uuid.UUID) -> SellerResponse:
        seller = await self.sellers.reactivate(seller_id)
        return SellerResponse.model_validate(seller)

    # --- shared -----------------------------------------------------------

    async def _to_document_response(
        self, document: SellerDocument
    ) -> SellerDocumentResponse:
        url = await storage.get_signed_url(
            document.cloudinary_public_id,
            resource_type=document.cloudinary_resource_type,
        )
        return SellerDocumentResponse(
            id=document.id,
            seller_id=document.seller_id,
            document_type=document.document_type,
            original_filename=document.original_filename,
            mime_type=document.mime_type,
            file_size=document.file_size,
            url=url,
            created_at=document.created_at,
        )
