"""Model → response schema. The table keeps the location as flat columns;
the API presents it as one nested object."""

from decimal import Decimal

from app.modules.sellers.seller_constants import required_documents
from app.modules.sellers.seller_model import Seller, SellerDocument
from app.modules.sellers.seller_schema import (
    SellerDocumentResponse,
    SellerLocation,
    SellerResponse,
)


def to_seller_response(seller: Seller, documents: list[SellerDocument]) -> SellerResponse:
    uploaded = {document.document_type for document in documents}
    return SellerResponse(
        id=seller.id,
        account_id=seller.account_id,
        business_name=seller.business_name,
        business_description=seller.business_description,
        business_phone=seller.business_phone,
        identity_document_type=seller.identity_document_type,
        identity_document_number=seller.identity_document_number,
        location=SellerLocation(
            country_code=seller.country_code,
            province=seller.province,
            district=seller.district,
            sector=seller.sector,
            cell=seller.cell,
            village=seller.village,
            street_address=seller.street_address,
            latitude=_to_float(seller.latitude),
            longitude=_to_float(seller.longitude),
            accuracy_m=seller.location_accuracy_m,
            source=seller.location_source,
        ),
        status=seller.status,
        status_reason=seller.status_reason,
        submitted_at=seller.submitted_at,
        reviewed_by_account_id=seller.reviewed_by_account_id,
        reviewed_at=seller.reviewed_at,
        approved_at=seller.approved_at,
        created_at=seller.created_at,
        documents=[
            SellerDocumentResponse(
                document_type=document.document_type,
                original_filename=document.original_filename,
                mime_type=document.mime_type,
                file_size=document.file_size,
                uploaded_at=document.updated_at,
            )
            for document in documents
        ],
        missing_documents=[
            document_type
            for document_type in required_documents(seller.identity_document_type)
            if document_type not in uploaded
        ],
    )


def _to_float(value: Decimal | None) -> float | None:
    # Coordinates are not money: a float is the right type for them in JSON.
    return float(value) if value is not None else None
