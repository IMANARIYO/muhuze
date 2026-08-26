import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin


class Seller(UUIDPKMixin, TimestampMixin, Base):
    """Business info for an Account that has become a seller. 1:1 with
    Account — identity verification (documents, admin approval) is a
    separate concern, tracked in seller_verification. An account can have a
    Seller row and still be blocked from withdrawing until that's approved.
    """

    __tablename__ = "sellers"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    store_name: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
