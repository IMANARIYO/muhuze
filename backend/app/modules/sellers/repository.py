import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sellers.models import Seller, SellerDocument, SellerStatus


class SellerRepository:
    """Data access for sellers. No business rules here — status-transition
    guards live in SellerService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, seller_id: uuid.UUID) -> Seller | None:
        result = await self.db.execute(select(Seller).where(Seller.id == seller_id))
        return result.scalar_one_or_none()

    async def get_by_account_id(self, account_id: uuid.UUID) -> Seller | None:
        result = await self.db.execute(
            select(Seller).where(Seller.account_id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_by_business_name(self, business_name: str) -> Seller | None:
        result = await self.db.execute(
            select(Seller).where(Seller.business_name == business_name)
        )
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str | None) -> list[Seller]:
        query = select(Seller).order_by(Seller.created_at.desc())
        if status is not None:
            query = query.where(Seller.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_ids(self, seller_ids: list[uuid.UUID]) -> dict[uuid.UUID, Seller]:
        if not seller_ids:
            return {}
        result = await self.db.execute(
            select(Seller).where(Seller.id.in_(seller_ids))
        )
        return {s.id: s for s in result.scalars().all()}

    async def create(
        self,
        *,
        account_id: uuid.UUID,
        business_name: str,
        business_description: str | None,
    ) -> Seller:
        seller = Seller(
            account_id=account_id,
            business_name=business_name,
            business_description=business_description,
            status=SellerStatus.DRAFT,
        )
        self.db.add(seller)
        await self.db.flush()
        await self.db.refresh(seller)
        return seller

    async def update_profile(
        self, seller: Seller, *, business_name: str, business_description: str | None
    ) -> Seller:
        seller.business_name = business_name
        seller.business_description = business_description
        await self.db.flush()
        await self.db.refresh(seller)
        return seller

    async def mark_submitted(self, seller: Seller) -> Seller:
        seller.status = SellerStatus.PENDING_REVIEW
        seller.submitted_at = datetime.now(UTC)
        seller.rejection_reason = None
        await self.db.flush()
        await self.db.refresh(seller)
        return seller

    async def mark_approved(self, seller: Seller, *, reviewed_by: uuid.UUID) -> Seller:
        seller.status = SellerStatus.ACTIVE
        seller.reviewed_by = reviewed_by
        seller.reviewed_at = datetime.now(UTC)
        seller.rejection_reason = None
        await self.db.flush()
        await self.db.refresh(seller)
        return seller

    async def mark_rejected(
        self, seller: Seller, *, reviewed_by: uuid.UUID, reason: str
    ) -> Seller:
        seller.status = SellerStatus.REJECTED
        seller.reviewed_by = reviewed_by
        seller.reviewed_at = datetime.now(UTC)
        seller.rejection_reason = reason
        await self.db.flush()
        await self.db.refresh(seller)
        return seller

    async def mark_suspended(self, seller: Seller) -> Seller:
        seller.status = SellerStatus.SUSPENDED
        await self.db.flush()
        await self.db.refresh(seller)
        return seller

    async def mark_reactivated(self, seller: Seller) -> Seller:
        seller.status = SellerStatus.ACTIVE
        await self.db.flush()
        await self.db.refresh(seller)
        return seller

    async def mark_deactivated(self, seller: Seller) -> Seller:
        seller.status = SellerStatus.DEACTIVATED
        await self.db.flush()
        await self.db.refresh(seller)
        return seller


class SellerDocumentRepository:
    """Data access for seller documents. No business rules, no Cloudinary
    calls here — those live in SellerDocumentService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, document_id: uuid.UUID) -> SellerDocument | None:
        result = await self.db.execute(
            select(SellerDocument).where(SellerDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_by_seller_and_type(
        self, seller_id: uuid.UUID, document_type: str
    ) -> SellerDocument | None:
        result = await self.db.execute(
            select(SellerDocument).where(
                SellerDocument.seller_id == seller_id,
                SellerDocument.document_type == document_type,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_seller(self, seller_id: uuid.UUID) -> list[SellerDocument]:
        result = await self.db.execute(
            select(SellerDocument)
            .where(SellerDocument.seller_id == seller_id)
            .order_by(SellerDocument.document_type)
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        seller_id: uuid.UUID,
        document_type: str,
        cloudinary_public_id: str,
        cloudinary_resource_type: str,
        original_filename: str | None,
        mime_type: str,
        file_size: int,
    ) -> SellerDocument:
        document = SellerDocument(
            seller_id=seller_id,
            document_type=document_type,
            cloudinary_public_id=cloudinary_public_id,
            cloudinary_resource_type=cloudinary_resource_type,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def replace(
        self,
        document: SellerDocument,
        *,
        cloudinary_public_id: str,
        cloudinary_resource_type: str,
        original_filename: str | None,
        mime_type: str,
        file_size: int,
    ) -> SellerDocument:
        document.cloudinary_public_id = cloudinary_public_id
        document.cloudinary_resource_type = cloudinary_resource_type
        document.original_filename = original_filename
        document.mime_type = mime_type
        document.file_size = file_size
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def delete(self, document: SellerDocument) -> None:
        await self.db.delete(document)
        await self.db.flush()
