"""Seller applications and their review.
Rules are documented in docs/features/004_sellers.md and README §15.

    draft → pending_review → active
    pending_review → rejected → (edit) → pending_review
    active ⇄ suspended    (by staff)
    active ⇄ deactivated  (by the seller)

Only an `active` seller may list products, sell, or withdraw; other features
ask `get_active_seller`. Every status change is written to the history.
Every public method is one unit of work and commits it.
"""

import uuid
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utc_now
from app.core.logging import get_logger
from app.infrastructure.storage.file_storage import (
    FileStorage,
    FileStorageError,
    StoredFile,
)
from app.modules.authorization.authorization_constants import SystemRole
from app.modules.authorization.authorization_service import AuthorizationService
from app.modules.sellers.seller_constants import (
    DOCUMENT_MAX_BYTES,
    DOCUMENT_SIGNATURES,
    DOCUMENT_URL_EXPIRES_SECONDS,
    EDITABLE_STATUSES,
    ORIGINAL_FILENAME_MAX_LENGTH,
    SellerDocumentType,
    SellerStatus,
    required_documents,
)
from app.modules.sellers.seller_exceptions import (
    BusinessNameTakenError,
    DocumentTooLargeError,
    FileStorageUnavailableError,
    InvalidDocumentFileError,
    MissingSellerDocumentsError,
    OwnApplicationReviewError,
    SellerAlreadyExistsError,
    SellerApplicationNotFoundError,
    SellerDocumentNotFoundError,
    SellerNotActiveError,
    SellerNotEditableError,
    SellerNotFoundError,
    SellerStatusConflictError,
)
from app.modules.sellers.seller_mapper import to_seller_response
from app.modules.sellers.seller_model import Seller, SellerDocument, SellerStatusHistory
from app.modules.sellers.seller_repository import SellerRepository
from app.modules.sellers.seller_schema import (
    DocumentUrlResponse,
    SellerApplicationRequest,
    SellerListFilters,
    SellerLocation,
    SellerResponse,
    SellerStatusHistoryResponse,
    SellerSummaryResponse,
    SellerUpdateRequest,
)
from app.shared.responses.pagination import Page, PaginationParams

logger = get_logger(__name__)

BUSINESS_NAME_INDEX = "uq_sellers_business_name_lower"


def open_shop_ids() -> Select:
    """The ids of sellers whose shops buyers may see, as a subquery.

    For other features' LIST queries, which must leave out the products of
    sellers who aren't open without loading sellers one by one:

        .where(Product.seller_id.in_(open_shop_ids()))

    The rule itself ("open" means `active`) stays here, in one place.
    """
    return select(Seller.id).where(Seller.status == SellerStatus.ACTIVE.value)


class SellerService:
    def __init__(
        self,
        session: AsyncSession,
        authorization: AuthorizationService,
        file_storage: FileStorage,
    ) -> None:
        self._session = session
        self._authorization = authorization
        self._file_storage = file_storage
        self._repository = SellerRepository(session)

    # ── Used by other features ───────────────────────────────────────────

    async def get_active_seller(self, account_id: uuid.UUID) -> Seller:
        """The account's seller, if it may trade right now. The single place
        that answers "can this account sell?" (README §15)."""
        seller = await self._repository.get_by_account(account_id)
        if seller is None or seller.status != SellerStatus.ACTIVE:
            raise SellerNotActiveError()
        return seller

    async def get_open_shop(self, seller_id: uuid.UUID) -> Seller:
        """A seller whose shop buyers may see. Any other seller looks exactly
        like one that doesn't exist, so shop pages reveal nothing about
        applications under review or suspended sellers."""
        seller = await self._repository.get(seller_id)
        if seller is None or seller.status != SellerStatus.ACTIVE:
            raise SellerNotFoundError()
        return seller

    # ── The seller's own application ─────────────────────────────────────

    async def apply(
        self, *, account_id: uuid.UUID, payload: SellerApplicationRequest
    ) -> SellerResponse:
        """Start an application as a draft. An account has at most one, forever."""
        if await self._repository.get_by_account(account_id) is not None:
            raise SellerAlreadyExistsError()
        if await self._repository.business_name_exists(payload.business_name):
            raise BusinessNameTakenError()

        seller = Seller(
            account_id=account_id,
            business_name=payload.business_name,
            business_description=payload.business_description or None,
            business_phone=payload.business_phone,
            identity_document_type=payload.identity_document_type.value,
            identity_document_number=payload.identity_document_number,
            status=SellerStatus.DRAFT.value,
        )
        _apply_location(seller, payload.location)
        try:
            await self._repository.add(seller)
        except IntegrityError as exc:
            # Lost a race: a concurrent request used the account or the name first.
            await self._session.rollback()
            raise _duplicate_error(exc) from exc
        await self._record(seller, from_status=None, changed_by=account_id)
        await self._session.commit()
        logger.info("seller application started", extra={"seller_id": str(seller.id)})
        return to_seller_response(seller, [])

    async def get_own(self, account_id: uuid.UUID) -> SellerResponse:
        seller = await self._own(account_id)
        return to_seller_response(seller, await self._repository.list_documents(seller.id))

    async def update_own(
        self, *, account_id: uuid.UUID, payload: SellerUpdateRequest
    ) -> SellerResponse:
        seller = await self._own_editable(account_id)
        # mode="json": enum members become their plain string values.
        changes = payload.model_dump(mode="json", exclude_unset=True, exclude={"location"})

        new_name = changes.get("business_name")
        if new_name is not None and await self._repository.business_name_exists(
            new_name, except_seller_id=seller.id
        ):
            raise BusinessNameTakenError()
        if "business_description" in changes:
            changes["business_description"] = changes["business_description"] or None
        for field, value in changes.items():
            setattr(seller, field, value)
        if payload.location is not None:
            _apply_location(seller, payload.location)

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _duplicate_error(exc) from exc
        logger.info("seller application updated", extra={"seller_id": str(seller.id)})
        return to_seller_response(seller, await self._repository.list_documents(seller.id))

    async def upload_document(
        self,
        *,
        account_id: uuid.UUID,
        document_type: SellerDocumentType,
        content: bytes,
        filename: str | None,
    ) -> SellerResponse:
        """Store a document privately. Uploading a type again replaces the file."""
        seller = await self._own_editable(account_id)
        if len(content) > DOCUMENT_MAX_BYTES:
            raise DocumentTooLargeError(
                f"The file is larger than {DOCUMENT_MAX_BYTES // (1024 * 1024)} MB"
            )
        mime_type = _detect_mime_type(content)

        try:
            stored = await self._file_storage.upload_private(
                content, folder=f"muhuze/sellers/{seller.id}"
            )
        except FileStorageError as exc:
            logger.exception("seller document upload failed", extra={"seller_id": str(seller.id)})
            raise FileStorageUnavailableError() from exc

        document = await self._repository.get_document(seller.id, document_type.value)
        replaced = _stored_file(document) if document is not None else None
        if document is None:
            document = SellerDocument(seller_id=seller.id, document_type=document_type.value)
        document.storage_public_id = stored.public_id
        document.storage_resource_type = stored.resource_type
        document.storage_format = stored.format
        document.original_filename = (filename or "")[:ORIGINAL_FILENAME_MAX_LENGTH] or None
        document.mime_type = mime_type
        document.file_size = len(content)
        if replaced is None:
            await self._repository.add_document(document)
        await self._session.commit()

        if replaced is not None:
            await self._discard(replaced, seller)
        logger.info(
            "seller document uploaded",
            extra={"seller_id": str(seller.id), "document_type": document_type.value},
        )
        return to_seller_response(seller, await self._repository.list_documents(seller.id))

    async def delete_document(
        self, *, account_id: uuid.UUID, document_type: SellerDocumentType
    ) -> SellerResponse:
        seller = await self._own_editable(account_id)
        document = await self._repository.get_document(seller.id, document_type.value)
        if document is None:
            raise SellerDocumentNotFoundError()
        stored = _stored_file(document)
        await self._repository.delete_document(document)
        await self._session.commit()
        await self._discard(stored, seller)
        return to_seller_response(seller, await self._repository.list_documents(seller.id))

    async def get_own_document_url(
        self, *, account_id: uuid.UUID, document_type: SellerDocumentType
    ) -> DocumentUrlResponse:
        seller = await self._own(account_id)
        return await self._document_url(seller, document_type)

    async def submit(self, account_id: uuid.UUID) -> SellerResponse:
        """Send the application for review. It can't be edited while it waits."""
        seller = await self._own(account_id, for_update=True)
        documents = await self._repository.list_documents(seller.id)
        self._require_status(
            seller,
            EDITABLE_STATUSES,
            "Only a draft or a rejected application can be submitted",
        )
        uploaded = {document.document_type for document in documents}
        missing = [
            document_type.value
            for document_type in required_documents(seller.identity_document_type)
            if document_type not in uploaded
        ]
        if missing:
            raise MissingSellerDocumentsError(
                f"Upload these documents before submitting: {', '.join(missing)}"
            )

        seller.submitted_at = utc_now()
        await self._change_status(seller, SellerStatus.PENDING_REVIEW, changed_by=account_id)
        await self._session.commit()
        logger.info("seller application submitted", extra={"seller_id": str(seller.id)})
        return to_seller_response(seller, documents)

    async def deactivate(self, account_id: uuid.UUID) -> SellerResponse:
        """The seller closes their own shop. They can reopen it themselves."""
        seller = await self._own(account_id, for_update=True)
        self._require_status(seller, {SellerStatus.ACTIVE}, "Only an active seller can deactivate")
        await self._change_status(seller, SellerStatus.DEACTIVATED, changed_by=account_id)
        await self._session.commit()
        logger.info("seller deactivated", extra={"seller_id": str(seller.id)})
        return to_seller_response(seller, await self._repository.list_documents(seller.id))

    async def reactivate(self, account_id: uuid.UUID) -> SellerResponse:
        seller = await self._own(account_id, for_update=True)
        self._require_status(
            seller, {SellerStatus.DEACTIVATED}, "Only a deactivated seller can reactivate"
        )
        await self._change_status(seller, SellerStatus.ACTIVE, changed_by=account_id)
        await self._session.commit()
        logger.info("seller reactivated", extra={"seller_id": str(seller.id)})
        return to_seller_response(seller, await self._repository.list_documents(seller.id))

    # ── Staff: reading ───────────────────────────────────────────────────

    async def list_sellers(
        self, pagination: PaginationParams, filters: SellerListFilters
    ) -> Page[SellerSummaryResponse]:
        sellers, total = await self._repository.list_sellers(
            pagination,
            status=filters.status.value if filters.status else None,
            search=filters.q.strip() if filters.q else None,
            sort=filters.sort,
        )
        items = [SellerSummaryResponse.model_validate(seller) for seller in sellers]
        return Page[SellerSummaryResponse].build(items, total, pagination)

    async def get_seller(self, seller_id: uuid.UUID) -> SellerResponse:
        seller = await self._existing(seller_id)
        return to_seller_response(seller, await self._repository.list_documents(seller.id))

    async def get_document_url(
        self, *, seller_id: uuid.UUID, document_type: SellerDocumentType
    ) -> DocumentUrlResponse:
        return await self._document_url(await self._existing(seller_id), document_type)

    async def list_history(
        self, seller_id: uuid.UUID, pagination: PaginationParams
    ) -> Page[SellerStatusHistoryResponse]:
        seller = await self._existing(seller_id)
        entries, total = await self._repository.list_history(seller.id, pagination)
        items = [SellerStatusHistoryResponse.model_validate(entry) for entry in entries]
        return Page[SellerStatusHistoryResponse].build(items, total, pagination)

    # ── Staff: decisions ─────────────────────────────────────────────────

    async def approve(self, *, seller_id: uuid.UUID, reviewer_id: uuid.UUID) -> SellerResponse:
        """Approve a waiting application: the seller becomes active and the
        account receives the `seller` role, in one transaction."""
        seller = await self._for_review(seller_id, reviewer_id)
        now = utc_now()
        seller.reviewed_by_account_id = reviewer_id
        seller.reviewed_at = now
        if seller.approved_at is None:
            seller.approved_at = now
        await self._change_status(seller, SellerStatus.ACTIVE, changed_by=reviewer_id)
        await self._authorization.assign_role(
            account_id=seller.account_id,
            role_name=SystemRole.SELLER.value,
            granted_by=reviewer_id,
        )
        await self._session.commit()
        logger.info(
            "seller approved",
            extra={"seller_id": str(seller.id), "by_account_id": str(reviewer_id)},
        )
        return to_seller_response(seller, await self._repository.list_documents(seller.id))

    async def reject(
        self, *, seller_id: uuid.UUID, reviewer_id: uuid.UUID, reason: str
    ) -> SellerResponse:
        """Reject a waiting application. The seller sees the reason, and can
        edit and submit again."""
        seller = await self._for_review(seller_id, reviewer_id)
        seller.reviewed_by_account_id = reviewer_id
        seller.reviewed_at = utc_now()
        await self._change_status(
            seller, SellerStatus.REJECTED, changed_by=reviewer_id, reason=reason
        )
        await self._session.commit()
        logger.info(
            "seller rejected",
            extra={"seller_id": str(seller.id), "by_account_id": str(reviewer_id)},
        )
        return to_seller_response(seller, await self._repository.list_documents(seller.id))

    async def suspend(
        self, *, seller_id: uuid.UUID, staff_id: uuid.UUID, reason: str
    ) -> SellerResponse:
        """Block an active seller from trading. The account can still log in and buy."""
        seller = await self._existing(seller_id, for_update=True)
        self._require_status(
            seller, {SellerStatus.ACTIVE}, "Only an active seller can be suspended"
        )
        await self._change_status(
            seller, SellerStatus.SUSPENDED, changed_by=staff_id, reason=reason
        )
        await self._session.commit()
        logger.info(
            "seller suspended", extra={"seller_id": str(seller.id), "by_account_id": str(staff_id)}
        )
        return to_seller_response(seller, await self._repository.list_documents(seller.id))

    async def reinstate(self, *, seller_id: uuid.UUID, staff_id: uuid.UUID) -> SellerResponse:
        seller = await self._existing(seller_id, for_update=True)
        self._require_status(
            seller, {SellerStatus.SUSPENDED}, "Only a suspended seller can be reinstated"
        )
        await self._change_status(seller, SellerStatus.ACTIVE, changed_by=staff_id)
        await self._session.commit()
        logger.info(
            "seller reinstated",
            extra={"seller_id": str(seller.id), "by_account_id": str(staff_id)},
        )
        return to_seller_response(seller, await self._repository.list_documents(seller.id))

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _own(self, account_id: uuid.UUID, *, for_update: bool = False) -> Seller:
        seller = await self._repository.get_by_account(account_id, for_update=for_update)
        if seller is None:
            raise SellerApplicationNotFoundError()
        return seller

    async def _own_editable(self, account_id: uuid.UUID) -> Seller:
        seller = await self._own(account_id, for_update=True)
        if seller.status not in EDITABLE_STATUSES:
            raise SellerNotEditableError()
        return seller

    async def _existing(self, seller_id: uuid.UUID, *, for_update: bool = False) -> Seller:
        seller = await self._repository.get(seller_id, for_update=for_update)
        if seller is None:
            raise SellerNotFoundError()
        return seller

    async def _for_review(self, seller_id: uuid.UUID, reviewer_id: uuid.UUID) -> Seller:
        seller = await self._existing(seller_id, for_update=True)
        if seller.account_id == reviewer_id:
            raise OwnApplicationReviewError()
        self._require_status(
            seller,
            {SellerStatus.PENDING_REVIEW},
            "Only an application waiting for review can be approved or rejected",
        )
        return seller

    @staticmethod
    def _require_status(seller: Seller, allowed: set | frozenset, message: str) -> None:
        if seller.status not in allowed:
            raise SellerStatusConflictError(message)

    async def _change_status(
        self,
        seller: Seller,
        to_status: SellerStatus,
        *,
        changed_by: uuid.UUID,
        reason: str | None = None,
    ) -> None:
        from_status = seller.status
        seller.status = to_status.value
        # The reason belongs to the current status: it is cleared when the
        # seller moves on (resubmits, is reinstated, …).
        seller.status_reason = reason
        await self._record(seller, from_status=from_status, changed_by=changed_by, reason=reason)

    async def _record(
        self,
        seller: Seller,
        *,
        from_status: str | None,
        changed_by: uuid.UUID,
        reason: str | None = None,
    ) -> None:
        await self._repository.add_history(
            SellerStatusHistory(
                seller_id=seller.id,
                from_status=from_status,
                to_status=seller.status,
                reason=reason,
                changed_by_account_id=changed_by,
            )
        )

    async def _document_url(
        self, seller: Seller, document_type: SellerDocumentType
    ) -> DocumentUrlResponse:
        document = await self._repository.get_document(seller.id, document_type.value)
        if document is None:
            raise SellerDocumentNotFoundError()
        try:
            url = self._file_storage.private_url(
                _stored_file(document), expires_in=DOCUMENT_URL_EXPIRES_SECONDS
            )
        except FileStorageError as exc:
            raise FileStorageUnavailableError() from exc
        return DocumentUrlResponse(url=url, expires_in=DOCUMENT_URL_EXPIRES_SECONDS)

    async def _discard(self, stored: StoredFile, seller: Seller) -> None:
        """Remove a file that no row points to any more. A failure is logged,
        not raised: the database is already correct, and the only cost is an
        orphaned private file."""
        try:
            await self._file_storage.delete(stored)
        except FileStorageError:
            logger.exception(
                "orphaned seller document left in storage", extra={"seller_id": str(seller.id)}
            )


def _apply_location(seller: Seller, location: SellerLocation) -> None:
    seller.country_code = location.country_code
    seller.province = location.province
    seller.district = location.district
    seller.sector = location.sector
    seller.cell = location.cell or None
    seller.village = location.village or None
    seller.street_address = location.street_address or None

    new_coordinates = (_to_decimal(location.latitude), _to_decimal(location.longitude))
    if new_coordinates != (seller.latitude, seller.longitude):
        seller.location_captured_at = utc_now() if location.latitude is not None else None
    seller.latitude, seller.longitude = new_coordinates
    seller.location_accuracy_m = location.accuracy_m
    seller.location_source = location.source.value if location.source else None


def _to_decimal(value: float | None) -> Decimal | None:
    # Six decimal places (about 11 cm), matching the column.
    return Decimal(str(round(value, 6))) if value is not None else None


def _detect_mime_type(content: bytes) -> str:
    for signature, mime_type in DOCUMENT_SIGNATURES:
        if content.startswith(signature):
            return mime_type
    raise InvalidDocumentFileError()


def _stored_file(document: SellerDocument) -> StoredFile:
    return StoredFile(
        public_id=document.storage_public_id,
        resource_type=document.storage_resource_type,
        format=document.storage_format,
    )


def _duplicate_error(exc: IntegrityError) -> Exception:
    if BUSINESS_NAME_INDEX in str(exc.orig):
        return BusinessNameTakenError()
    return SellerAlreadyExistsError()
