import enum

from sqlalchemy import DateTime, Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class InvestorStatus(str, enum.Enum):
    PENDING = "PENDING"
    DOCS_REQUESTED = "DOCS_REQUESTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class AccreditationType(str, enum.Enum):
    INCOME = "income"
    NET_WORTH = "net_worth"
    PROFESSIONAL = "professional_certification"
    ENTITY = "entity"


class Investor(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "investors"

    # AES-256-GCM encrypted fields (stored as base64)
    encrypted_name: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_email: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_phone: Mapped[str | None] = mapped_column(Text, nullable=True)

    # SHA-256 hash for dedup lookups without decryption
    email_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )

    accreditation_type: Mapped[AccreditationType] = mapped_column(
        Enum(AccreditationType), nullable=False
    )

    status: Mapped[InvestorStatus] = mapped_column(
        Enum(InvestorStatus),
        nullable=False,
        default=InvestorStatus.PENDING,
        index=True,
    )

    # IP of submission for compliance audit trail
    intake_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Admin notes (unencrypted, internal only)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Provider reference ID (VerifyInvestor, Parallel Markets, etc.)
    verification_provider_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    verified_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_investors_status_created", "status", "created_at"),
    )
