import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.modules.auth.dependencies import get_current_account, require_role
from app.modules.auth.models import Account
from app.modules.sellers.controller import SellerController
from app.modules.sellers.dependencies import get_seller_controller
from app.modules.sellers.schemas import (
    RejectSellerRequest,
    SellerDocumentResponse,
    SellerRegistrationRequest,
    SellerResponse,
    SellerUpdateRequest,
    SuspendSellerRequest,
)
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/sellers", tags=["Sellers"])


# --- self-service ---------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
async def register(
    payload: SellerRegistrationRequest,
    account: Account = Depends(get_current_account),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerResponse]:
    """Create a seller profile for the caller's own account, in `draft`
    status. One seller profile per account — calling this twice is a 409.
    See sellers/docs/lifecycle.md for the full status state machine."""
    seller = await controller.register(account, payload)
    return success_response(data=seller, message="Seller profile created successfully")


@router.get("/me")
async def get_my_seller(
    account: Account = Depends(get_current_account),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerResponse]:
    """Get the caller's own seller profile."""
    seller = await controller.get_my_seller(account)
    return success_response(
        data=seller, message="Seller profile retrieved successfully"
    )


@router.patch("/me")
async def update_my_profile(
    payload: SellerUpdateRequest,
    account: Account = Depends(get_current_account),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerResponse]:
    """Update the caller's own seller profile. Only allowed while the
    seller is `draft` or `rejected` — once submitted, the information
    under review is locked."""
    seller = await controller.update_my_profile(account, payload)
    return success_response(data=seller, message="Seller profile updated successfully")


@router.post("/me/submit")
async def submit_for_review(
    account: Account = Depends(get_current_account),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerResponse]:
    """Submit the caller's own seller profile for admin review, moving it
    from `draft`/`rejected` to `pending_review`. Requires the required
    identity documents to already be uploaded (see /me/documents) — 422
    if any are missing."""
    seller = await controller.submit_for_review(account)
    return success_response(
        data=seller, message="Seller application submitted for review"
    )


@router.post("/me/deactivate")
async def deactivate(
    account: Account = Depends(get_current_account),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerResponse]:
    """Voluntarily deactivate the caller's own active seller account.
    Only allowed while `active`; deactivation is not reversible via the
    self-service API — re-registration requires admin involvement."""
    seller = await controller.deactivate(account)
    return success_response(data=seller, message="Seller account deactivated")


@router.post("/me/reactivate")
async def reactivate_mine(
    account: Account = Depends(get_current_account),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerResponse]:
    """Self-service reactivation: re-open the caller's own voluntarily
    `deactivated` seller account back to `active` with one click. Only
    `deactivated` -> `active`; a `suspended` seller must be reactivated by
    an admin (POST /sellers/{seller_id}/reactivate)."""
    seller = await controller.reactivate_my_seller(account)
    return success_response(data=seller, message="Seller account reactivated")


@router.post("/me/documents", status_code=status.HTTP_201_CREATED)
async def upload_my_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    account: Account = Depends(get_current_account),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerDocumentResponse]:
    """Upload (or replace, if one of this `document_type` already exists)
    an identity-verification document for the caller's own seller
    profile. `document_type` is one of `national_id_front`,
    `national_id_back`, `passport`, `driving_license`. Stored privately —
    `url` in the response is a short-lived signed URL, never a public
    link. See sellers/docs/documents.md."""
    document = await controller.upload_my_document(
        account, document_type=document_type, file=file
    )
    return success_response(data=document, message="Document uploaded successfully")


@router.get("/me/documents")
async def list_my_documents(
    account: Account = Depends(get_current_account),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[list[SellerDocumentResponse]]:
    """List the caller's own uploaded identity-verification documents."""
    documents = await controller.list_my_documents(account)
    return success_response(data=documents, message="Documents retrieved successfully")


@router.delete("/me/documents/{document_id}")
async def delete_my_document(
    document_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[None]:
    """Delete one of the caller's own uploaded documents, including its
    Cloudinary asset."""
    await controller.delete_my_document(account, document_id)
    return success_response(message="Document deleted successfully")


# --- admin ------------------------------------------------------------------


@router.get("")
async def list_sellers(
    status_filter: str | None = Query(default=None, alias="status"),
    admin: Account = Depends(require_role("admin")),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[list[SellerResponse]]:
    """List all sellers, optionally filtered by status
    (`?status=pending_review`). Admin only."""
    sellers = await controller.list_sellers(status=status_filter)
    return success_response(data=sellers, message="Sellers retrieved successfully")


@router.get("/{seller_id}")
async def get_seller(
    seller_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerResponse]:
    """Get any seller by id. Admin only."""
    seller = await controller.get_seller(seller_id)
    return success_response(data=seller, message="Seller retrieved successfully")


@router.get("/{seller_id}/documents")
async def list_seller_documents(
    seller_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[list[SellerDocumentResponse]]:
    """List a specific seller's uploaded identity-verification documents,
    for review during approval. Admin only."""
    documents = await controller.list_seller_documents(seller_id)
    return success_response(data=documents, message="Documents retrieved successfully")


@router.post("/{seller_id}/approve")
async def approve(
    seller_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerResponse]:
    """Approve a `pending_review` seller, moving it to `active` and
    granting the `seller` role to its account. Admin only."""
    seller = await controller.approve(seller_id, admin)
    return success_response(data=seller, message="Seller approved successfully")


@router.post("/{seller_id}/reject")
async def reject(
    seller_id: uuid.UUID,
    payload: RejectSellerRequest,
    admin: Account = Depends(require_role("admin")),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerResponse]:
    """Reject a `pending_review` seller with a reason, moving it to
    `rejected` (the seller can edit and resubmit). Admin only."""
    seller = await controller.reject(seller_id, admin, payload)
    return success_response(data=seller, message="Seller rejected")


@router.post("/{seller_id}/suspend")
async def suspend(
    seller_id: uuid.UUID,
    payload: SuspendSellerRequest,
    admin: Account = Depends(require_role("admin")),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerResponse]:
    """Suspend an `active` seller, moving it to `suspended`. Does not
    revoke the `seller` role — see sellers/docs/lifecycle.md for why role
    and status are kept independent. Admin only."""
    seller = await controller.suspend(seller_id, payload)
    return success_response(data=seller, message="Seller suspended")


@router.post("/{seller_id}/reactivate")
async def reactivate(
    seller_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse[SellerResponse]:
    """Reactivate a `suspended` seller back to `active`. Admin only."""
    seller = await controller.reactivate(seller_id)
    return success_response(data=seller, message="Seller reactivated")
