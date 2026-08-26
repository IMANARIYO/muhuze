import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin


class SellerStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class SellerDocumentType(StrEnum):
    NATIONAL_ID_FRONT = "national_id_front"
    NATIONAL_ID_BACK = "national_id_back"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"


class Seller(UUIDPKMixin, TimestampMixin, Base):
    """Business profile for an Account that has applied to sell. 1:0..1 with
    Account — deliberately never merged into it. Account answers "who is
    this person and can they log in"; Seller answers "how does this
    account operate as a seller, and is that currently trusted". A Seller
    row existing says nothing about whether it's approved — see `status`.

    Never hard-deleted: once a seller has orders/revenue/wallet history,
    deleting the row would destroy financial history. Lifecycle is always
    a status transition (see SellerStatus), never a DELETE.
    """

    __tablename__ = "sellers"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    business_name: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True
    )
    business_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SellerStatus.DRAFT, index=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class SellerDocument(UUIDPKMixin, TimestampMixin, Base):
    """One identity-verification document. At most one row per
    (seller_id, document_type) — re-uploading the same type replaces it
    (old Cloudinary asset deleted) rather than keeping version history.
    That's a deliberate simplification, not an oversight — see
    sellers/docs/documents.md.

    Stored with Cloudinary delivery_type="authenticated": never a public
    URL. Access is always through a freshly-signed URL generated at
    request time (app/core/storage.py::get_signed_url), never persisted.
    """

    __tablename__ = "seller_documents"
    __table_args__ = (
        UniqueConstraint("seller_id", "document_type", name="uq_seller_documents_type"),
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    cloudinary_public_id: Mapped[str] = mapped_column(String(255), nullable=False)
    cloudinary_resource_type: Mapped[str] = mapped_column(String(20), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
