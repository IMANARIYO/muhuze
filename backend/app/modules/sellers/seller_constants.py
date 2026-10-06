from enum import StrEnum


class SellerStatus(StrEnum):
    DRAFT = "draft"  # application started, not sent yet
    PENDING_REVIEW = "pending_review"  # sent, waiting for an admin
    ACTIVE = "active"  # approved: may list products, sell, and withdraw
    REJECTED = "rejected"  # declined with a reason; can be edited and sent again
    SUSPENDED = "suspended"  # blocked by an admin
    DEACTIVATED = "deactivated"  # closed by the seller; the seller can reopen it


# The seller may change the application and its documents only in these states.
EDITABLE_STATUSES = frozenset({SellerStatus.DRAFT, SellerStatus.REJECTED})


class IdentityDocumentType(StrEnum):
    NATIONAL_ID = "national_id"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"


class SellerDocumentType(StrEnum):
    IDENTITY_FRONT = "identity_front"
    IDENTITY_BACK = "identity_back"
    BUSINESS_REGISTRATION = "business_registration"  # optional
    TIN_CERTIFICATE = "tin_certificate"  # optional


class LocationSource(StrEnum):
    DEVICE = "device"  # read from the device ("detect my location")
    MANUAL = "manual"  # a pin placed by the seller


def required_documents(identity_document_type: str) -> tuple[SellerDocumentType, ...]:
    """The files an application must have before it can be sent for review."""
    if identity_document_type == IdentityDocumentType.PASSPORT:
        # A passport's identity page is a single side.
        return (SellerDocumentType.IDENTITY_FRONT,)
    return (SellerDocumentType.IDENTITY_FRONT, SellerDocumentType.IDENTITY_BACK)


BUSINESS_NAME_MIN_LENGTH = 2
BUSINESS_NAME_MAX_LENGTH = 150
BUSINESS_DESCRIPTION_MAX_LENGTH = 2000
IDENTITY_DOCUMENT_NUMBER_MIN_LENGTH = 3
IDENTITY_DOCUMENT_NUMBER_MAX_LENGTH = 50
ADDRESS_PART_MAX_LENGTH = 100
STREET_ADDRESS_MAX_LENGTH = 255
STATUS_REASON_MIN_LENGTH = 5
STATUS_REASON_MAX_LENGTH = 500
DEFAULT_COUNTRY_CODE = "RW"

# Uploaded documents.
DOCUMENT_MAX_BYTES = 5 * 1024 * 1024
# The type is decided from the file's first bytes, never from what the client claims.
DOCUMENT_SIGNATURES = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"%PDF-", "application/pdf"),
)
# How long a signed link to a document keeps working.
DOCUMENT_URL_EXPIRES_SECONDS = 300
ORIGINAL_FILENAME_MAX_LENGTH = 255

SEARCH_QUERY_MAX_LENGTH = 100
