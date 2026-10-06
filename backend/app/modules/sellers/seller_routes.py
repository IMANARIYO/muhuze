import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse

from app.modules.auth.auth_dependencies import get_current_account
from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import require_permission
from app.modules.sellers.seller_constants import DOCUMENT_MAX_BYTES, SellerDocumentType
from app.modules.sellers.seller_dependencies import get_seller_service
from app.modules.sellers.seller_permissions import SELLER_READ, SELLER_REVIEW, SELLER_SUSPEND
from app.modules.sellers.seller_schema import (
    DocumentUrlResponse,
    SellerApplicationRequest,
    SellerListFilters,
    SellerResponse,
    SellerStatusHistoryResponse,
    SellerSummaryResponse,
    SellerUpdateRequest,
    StatusReasonRequest,
)
from app.modules.sellers.seller_service import SellerService
from app.shared.responses.api_response import APIResponse, success_response
from app.shared.responses.pagination import Page, PaginationParams

seller_router = APIRouter(prefix="/sellers", tags=["Sellers"])

ServiceDep = Annotated[SellerService, Depends(get_seller_service)]
CurrentAccountDep = Annotated[Account, Depends(get_current_account)]
# Depends(), not Query(): FastAPI accepts only ONE Query() parameter model per
# endpoint, and list endpoints here combine pagination with filters.
PaginationDep = Annotated[PaginationParams, Depends()]
FiltersDep = Annotated[SellerListFilters, Depends()]


def allowed(permission) -> type[Account]:
    return Annotated[Account, Depends(require_permission(permission))]


# ── The caller's own application ─────────────────────────────────────────
# These act on the caller's own seller record, so they need a login only.
# They are declared before the `/{seller_id}` routes so "me" is never read
# as an id.


@seller_router.post(
    "/me", response_model=APIResponse[SellerResponse], status_code=status.HTTP_201_CREATED
)
async def apply_to_sell(
    payload: SellerApplicationRequest, account: CurrentAccountDep, service: ServiceDep
) -> JSONResponse:
    """Start a seller application as a draft. Upload the documents, then submit it."""
    seller = await service.apply(account_id=account.id, payload=payload)
    return success_response(
        data=seller,
        message="Application started. Upload your documents, then submit it for review.",
        status_code=status.HTTP_201_CREATED,
    )


@seller_router.get("/me", response_model=APIResponse[SellerResponse])
async def get_my_seller(account: CurrentAccountDep, service: ServiceDep) -> JSONResponse:
    """The caller's seller application, its status, and its documents."""
    return success_response(data=await service.get_own(account.id), message="Seller retrieved")


@seller_router.patch("/me", response_model=APIResponse[SellerResponse])
async def update_my_seller(
    payload: SellerUpdateRequest, account: CurrentAccountDep, service: ServiceDep
) -> JSONResponse:
    """Change the application. Only while it is a draft or after a rejection."""
    seller = await service.update_own(account_id=account.id, payload=payload)
    return success_response(data=seller, message="Application updated")


@seller_router.put("/me/documents/{document_type}", response_model=APIResponse[SellerResponse])
async def upload_my_document(
    document_type: SellerDocumentType,
    file: UploadFile,
    account: CurrentAccountDep,
    service: ServiceDep,
) -> JSONResponse:
    """Upload a document (JPEG, PNG, or PDF, up to 5 MB) as multipart form
    field `file`. Uploading the same type again replaces it."""
    # Read one byte past the limit: enough to know the file is too large
    # without holding an arbitrarily large upload in memory.
    content = await file.read(DOCUMENT_MAX_BYTES + 1)
    seller = await service.upload_document(
        account_id=account.id,
        document_type=document_type,
        content=content,
        filename=file.filename,
    )
    return success_response(data=seller, message="Document uploaded")


@seller_router.delete("/me/documents/{document_type}", response_model=APIResponse[SellerResponse])
async def delete_my_document(
    document_type: SellerDocumentType, account: CurrentAccountDep, service: ServiceDep
) -> JSONResponse:
    seller = await service.delete_document(account_id=account.id, document_type=document_type)
    return success_response(data=seller, message="Document removed")


@seller_router.get(
    "/me/documents/{document_type}/url", response_model=APIResponse[DocumentUrlResponse]
)
async def get_my_document_url(
    document_type: SellerDocumentType, account: CurrentAccountDep, service: ServiceDep
) -> JSONResponse:
    """A private link to one of the caller's own documents. It expires in a few minutes."""
    url = await service.get_own_document_url(account_id=account.id, document_type=document_type)
    return success_response(data=url, message="Document link created")


@seller_router.post("/me/submit", response_model=APIResponse[SellerResponse])
async def submit_my_application(account: CurrentAccountDep, service: ServiceDep) -> JSONResponse:
    """Send the application for review. It can't be changed while it waits."""
    return success_response(
        data=await service.submit(account.id), message="Application submitted for review"
    )


@seller_router.post("/me/deactivate", response_model=APIResponse[SellerResponse])
async def deactivate_my_seller(account: CurrentAccountDep, service: ServiceDep) -> JSONResponse:
    """Close your own shop. You can reopen it yourself."""
    return success_response(data=await service.deactivate(account.id), message="Shop closed")


@seller_router.post("/me/reactivate", response_model=APIResponse[SellerResponse])
async def reactivate_my_seller(account: CurrentAccountDep, service: ServiceDep) -> JSONResponse:
    """Reopen a shop you closed yourself."""
    return success_response(data=await service.reactivate(account.id), message="Shop reopened")


# ── Staff ────────────────────────────────────────────────────────────────


@seller_router.get("", response_model=APIResponse[Page[SellerSummaryResponse]])
async def list_sellers(
    _: allowed(SELLER_READ),
    pagination: PaginationDep,
    filters: FiltersDep,
    service: ServiceDep,
) -> JSONResponse:
    """Every seller. Use `status=pending_review` for the review queue."""
    page = await service.list_sellers(pagination, filters)
    return success_response(data=page, message="Sellers retrieved")


@seller_router.get("/{seller_id}", response_model=APIResponse[SellerResponse])
async def get_seller(
    _: allowed(SELLER_READ), seller_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """One seller's full application, including identity details."""
    return success_response(data=await service.get_seller(seller_id), message="Seller retrieved")


@seller_router.get(
    "/{seller_id}/documents/{document_type}/url", response_model=APIResponse[DocumentUrlResponse]
)
async def get_seller_document_url(
    _: allowed(SELLER_READ),
    seller_id: uuid.UUID,
    document_type: SellerDocumentType,
    service: ServiceDep,
) -> JSONResponse:
    """A private link to one of a seller's documents. It expires in a few minutes."""
    url = await service.get_document_url(seller_id=seller_id, document_type=document_type)
    return success_response(data=url, message="Document link created")


@seller_router.get(
    "/{seller_id}/history", response_model=APIResponse[Page[SellerStatusHistoryResponse]]
)
async def list_seller_history(
    _: allowed(SELLER_READ), seller_id: uuid.UUID, pagination: PaginationDep, service: ServiceDep
) -> JSONResponse:
    """Every status change of a seller, newest first: who, when, and why."""
    page = await service.list_history(seller_id, pagination)
    return success_response(data=page, message="Seller history retrieved")


@seller_router.post("/{seller_id}/approve", response_model=APIResponse[SellerResponse])
async def approve_seller(
    reviewer: allowed(SELLER_REVIEW), seller_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Approve a waiting application. The seller can then list products and sell."""
    seller = await service.approve(seller_id=seller_id, reviewer_id=reviewer.id)
    return success_response(data=seller, message="Seller approved")


@seller_router.post("/{seller_id}/reject", response_model=APIResponse[SellerResponse])
async def reject_seller(
    reviewer: allowed(SELLER_REVIEW),
    seller_id: uuid.UUID,
    payload: StatusReasonRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Reject a waiting application with a reason. The seller can edit and submit again."""
    seller = await service.reject(
        seller_id=seller_id, reviewer_id=reviewer.id, reason=payload.reason
    )
    return success_response(data=seller, message="Seller rejected")


@seller_router.post("/{seller_id}/suspend", response_model=APIResponse[SellerResponse])
async def suspend_seller(
    staff: allowed(SELLER_SUSPEND),
    seller_id: uuid.UUID,
    payload: StatusReasonRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Stop an active seller from trading. The account can still log in and buy."""
    seller = await service.suspend(seller_id=seller_id, staff_id=staff.id, reason=payload.reason)
    return success_response(data=seller, message="Seller suspended")


@seller_router.post("/{seller_id}/reinstate", response_model=APIResponse[SellerResponse])
async def reinstate_seller(
    staff: allowed(SELLER_SUSPEND), seller_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Let a suspended seller trade again."""
    seller = await service.reinstate(seller_id=seller_id, staff_id=staff.id)
    return success_response(data=seller, message="Seller reinstated")
