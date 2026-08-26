import contextlib
import uuid

from fastapi import UploadFile

from app.core import notifications, storage
from app.modules.auth.models import Account
from app.modules.auth.repository import AccountRepository, AuthorizationRepository
from app.modules.sellers.exceptions import (
    BusinessNameAlreadyTakenError,
    MissingRequiredDocumentsError,
    SellerAlreadyExistsError,
    SellerDocumentNotFoundError,
    SellerNotActiveError,
    SellerNotEditableError,
    SellerNotFoundError,
    SellerNotPendingReviewError,
    SellerNotSubmittableError,
    SellerNotSuspendedError,
)
from app.modules.sellers.models import (
    Seller,
    SellerDocument,
    SellerDocumentType,
    SellerStatus,
)
from app.modules.sellers.repository import SellerDocumentRepository, SellerRepository

DOCUMENT_CONTENT_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

# A seller must prove identity one of these ways: both sides of a national
# ID, or a single-document passport/driving license.
_IDENTITY_DOCUMENT_SETS: tuple[frozenset[str], ...] = (
    frozenset(
        {SellerDocumentType.NATIONAL_ID_FRONT, SellerDocumentType.NATIONAL_ID_BACK}
    ),
    frozenset({SellerDocumentType.PASSPORT}),
    frozenset({SellerDocumentType.DRIVING_LICENSE}),
)


def _has_required_documents(document_types: set[str]) -> bool:
    return any(required <= document_types for required in _IDENTITY_DOCUMENT_SETS)


class SellerService:
    """Business rules for the seller lifecycle: registration, submission,
    admin review, suspension, deactivation. Document upload is a separate
    concern — see SellerDocumentService."""

    def __init__(
        self,
        sellers: SellerRepository,
        documents: SellerDocumentRepository,
        accounts: AccountRepository,
        authorization: AuthorizationRepository,
    ) -> None:
        self.sellers = sellers
        self.documents = documents
        self.accounts = accounts
        self.authorization = authorization

    async def register(
        self, account: Account, *, business_name: str, business_description: str | None
    ) -> Seller:
        """A Seller row is at most one per account, full stop — even a
        rejected application is edited and resubmitted on the same row,
        never recreated. See sellers/docs/lifecycle.md."""
        if await self.sellers.get_by_account_id(account.id) is not None:
            raise SellerAlreadyExistsError()
        if await self.sellers.get_by_business_name(business_name) is not None:
            raise BusinessNameAlreadyTakenError()
        return await self.sellers.create(
            account_id=account.id,
            business_name=business_name,
            business_description=business_description,
        )

    async def get_my_seller(self, account_id: uuid.UUID) -> Seller:
        seller = await self.sellers.get_by_account_id(account_id)
        if seller is None:
            raise SellerNotFoundError()
        return seller

    async def get_seller_by_id(self, seller_id: uuid.UUID) -> Seller:
        seller = await self.sellers.get_by_id(seller_id)
        if seller is None:
            raise SellerNotFoundError()
        return seller

    async def list_sellers(self, *, status: str | None) -> list[Seller]:
        return await self.sellers.list_by_status(status)

    async def update_profile(
        self,
        account_id: uuid.UUID,
        *,
        business_name: str,
        business_description: str | None,
    ) -> Seller:
        seller = await self.get_my_seller(account_id)
        if seller.status not in (SellerStatus.DRAFT, SellerStatus.REJECTED):
            raise SellerNotEditableError()
        if business_name != seller.business_name:
            holder = await self.sellers.get_by_business_name(business_name)
            if holder is not None and holder.id != seller.id:
                raise BusinessNameAlreadyTakenError()
        return await self.sellers.update_profile(
            seller,
            business_name=business_name,
            business_description=business_description,
        )

    async def submit_for_review(self, account: Account) -> Seller:
        seller = await self.get_my_seller(account.id)
        if seller.status not in (SellerStatus.DRAFT, SellerStatus.REJECTED):
            raise SellerNotSubmittableError()

        documents = await self.documents.list_by_seller(seller.id)
        if not _has_required_documents({doc.document_type for doc in documents}):
            raise MissingRequiredDocumentsError()

        updated = await self.sellers.mark_submitted(seller)
        await notifications.send_email(
            to=account.email,
            subject="MUHUZE: seller application received",
            body=(
                f"We received your seller application for '{seller.business_name}' "
                "and will review it shortly."
            ),
        )
        return updated

    async def approve(
        self, seller_id: uuid.UUID, *, admin_account_id: uuid.UUID
    ) -> Seller:
        seller = await self.get_seller_by_id(seller_id)
        if seller.status != SellerStatus.PENDING_REVIEW:
            raise SellerNotPendingReviewError()

        updated = await self.sellers.mark_approved(seller, reviewed_by=admin_account_id)

        # The role represents "has been through seller approval at least
        # once"; Seller.status is the actual operational gate (see
        # sellers/docs/lifecycle.md — don't conflate the two).
        seller_role = await self.authorization.get_role_by_name("seller")
        if seller_role is not None:
            await self.authorization.assign_role(
                account_id=seller.account_id, role_id=seller_role.id
            )

        await self._notify_owner(
            seller,
            subject="MUHUZE: seller application approved",
            body=f"Congratulations — your seller account '{seller.business_name}' has been approved.",
        )
        return updated

    async def reject(
        self, seller_id: uuid.UUID, *, admin_account_id: uuid.UUID, reason: str
    ) -> Seller:
        seller = await self.get_seller_by_id(seller_id)
        if seller.status != SellerStatus.PENDING_REVIEW:
            raise SellerNotPendingReviewError()

        updated = await self.sellers.mark_rejected(
            seller, reviewed_by=admin_account_id, reason=reason
        )
        await self._notify_owner(
            seller,
            subject="MUHUZE: seller application needs changes",
            body=(
                f"Your seller application for '{seller.business_name}' was not approved. "
                f"Reason: {reason}. You may update your information and resubmit."
            ),
        )
        return updated

    async def suspend(self, seller_id: uuid.UUID, *, reason: str | None) -> Seller:
        seller = await self.get_seller_by_id(seller_id)
        if seller.status != SellerStatus.ACTIVE:
            raise SellerNotActiveError()

        updated = await self.sellers.mark_suspended(seller)
        body = (
            f"Your MUHUZE seller account '{seller.business_name}' has been suspended."
        )
        if reason:
            body += f" Reason: {reason}."
        await self._notify_owner(
            seller, subject="MUHUZE: seller account suspended", body=body
        )
        return updated

    async def reactivate(self, seller_id: uuid.UUID) -> Seller:
        seller = await self.get_seller_by_id(seller_id)
        if seller.status != SellerStatus.SUSPENDED:
            raise SellerNotSuspendedError()

        updated = await self.sellers.mark_reactivated(seller)
        await self._notify_owner(
            seller,
            subject="MUHUZE: seller account reactivated",
            body=f"Your MUHUZE seller account '{seller.business_name}' has been reactivated.",
        )
        return updated

    async def deactivate(self, account: Account) -> Seller:
        seller = await self.get_my_seller(account.id)
        if seller.status != SellerStatus.ACTIVE:
            raise SellerNotActiveError()

        updated = await self.sellers.mark_deactivated(seller)
        await notifications.send_email(
            to=account.email,
            subject="MUHUZE: seller account deactivated",
            body=(
                f"Your MUHUZE seller account '{seller.business_name}' has been "
                "deactivated at your request."
            ),
        )
        return updated

    async def _notify_owner(self, seller: Seller, *, subject: str, body: str) -> None:
        """Admin-initiated transitions (approve/reject/suspend/reactivate)
        only have the seller's account_id, not the account object — this
        looks it up. A missing account here would mean the FK is broken,
        not a normal case; silently skipping the email is the right call
        rather than failing the whole admin action over a notification."""
        account = await self.accounts.get_by_id(seller.account_id)
        if account is not None:
            await notifications.send_email(to=account.email, subject=subject, body=body)


class SellerDocumentService:
    """Business rules for uploading/managing seller verification
    documents. Cloudinary-backed via app/core/storage.py — see
    sellers/docs/documents.md for the upload/replace/failure-compensation
    design."""

    def __init__(
        self, sellers: SellerRepository, documents: SellerDocumentRepository
    ) -> None:
        self.sellers = sellers
        self.documents = documents

    async def upload_document(
        self, account_id: uuid.UUID, *, document_type: str, file: UploadFile
    ) -> SellerDocument:
        seller = await self.sellers.get_by_account_id(account_id)
        if seller is None:
            raise SellerNotFoundError()
        if seller.status not in (SellerStatus.DRAFT, SellerStatus.REJECTED):
            raise SellerNotEditableError()

        existing = await self.documents.get_by_seller_and_type(seller.id, document_type)

        uploaded = await storage.upload_file(
            file,
            folder="seller_verification",
            allowed_content_types=DOCUMENT_CONTENT_TYPES,
            max_size_bytes=MAX_DOCUMENT_SIZE_BYTES,
            delivery_type="authenticated",
        )

        try:
            if existing is not None:
                old_public_id = existing.cloudinary_public_id
                old_resource_type = existing.cloudinary_resource_type
                document = await self.documents.replace(
                    existing,
                    cloudinary_public_id=uploaded.public_id,
                    cloudinary_resource_type=uploaded.resource_type,
                    original_filename=file.filename,
                    mime_type=file.content_type or "application/octet-stream",
                    file_size=uploaded.bytes,
                )
                # Best-effort: the DB is already correct at this point, so a
                # failure here shouldn't fail the request — it just leaves
                # one harmless orphaned Cloudinary asset.
                with contextlib.suppress(Exception):
                    await storage.delete_file(
                        old_public_id,
                        resource_type=old_resource_type,
                        delivery_type="authenticated",
                    )
            else:
                document = await self.documents.create(
                    seller_id=seller.id,
                    document_type=document_type,
                    cloudinary_public_id=uploaded.public_id,
                    cloudinary_resource_type=uploaded.resource_type,
                    original_filename=file.filename,
                    mime_type=file.content_type or "application/octet-stream",
                    file_size=uploaded.bytes,
                )
        except Exception:
            # Cloudinary succeeded but the DB write failed — don't leave an
            # orphaned file with no database record pointing at it.
            with contextlib.suppress(Exception):
                await storage.delete_file(
                    uploaded.public_id,
                    resource_type=uploaded.resource_type,
                    delivery_type="authenticated",
                )
            raise

        return document

    async def list_documents(self, account_id: uuid.UUID) -> list[SellerDocument]:
        seller = await self.sellers.get_by_account_id(account_id)
        if seller is None:
            raise SellerNotFoundError()
        return await self.documents.list_by_seller(seller.id)

    async def list_documents_for_seller(
        self, seller_id: uuid.UUID
    ) -> list[SellerDocument]:
        """Admin path: seller already resolved by ID by the caller."""
        return await self.documents.list_by_seller(seller_id)

    async def delete_document(
        self, account_id: uuid.UUID, document_id: uuid.UUID
    ) -> None:
        seller = await self.sellers.get_by_account_id(account_id)
        if seller is None:
            raise SellerNotFoundError()
        document = await self._get_owned_document(seller.id, document_id)

        await self.documents.delete(document)
        with contextlib.suppress(Exception):
            await storage.delete_file(
                document.cloudinary_public_id,
                resource_type=document.cloudinary_resource_type,
                delivery_type="authenticated",
            )

    async def _get_owned_document(
        self, seller_id: uuid.UUID, document_id: uuid.UUID
    ) -> SellerDocument:
        document = await self.documents.get_by_id(document_id)
        if document is None or document.seller_id != seller_id:
            raise SellerDocumentNotFoundError()
        return document
