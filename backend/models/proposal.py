"""
NoblePort Proposal Model

Proposals with deposit enforcement, expiration, and signature tracking.
Status flow: DRAFT → SENT → SIGNED → DEPOSIT_PENDING → DEPOSIT_PAID → ACTIVE → COMPLETED/VOID

Key principle: Signature = intent, Payment = commitment.
A signed proposal does nothing until the deposit clears.
"""

from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class ProposalStatus(str, PyEnum):
    DRAFT = "draft"
    SENT = "sent"
    SIGNED = "signed"
    DEPOSIT_PENDING = "deposit_pending"
    DEPOSIT_PAID = "deposit_paid"
    ACTIVE = "active"
    COMPLETED = "completed"
    VOID = "void"
    REJECTED = "rejected"


class Proposal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "proposals"

    # Client Info
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_email: Mapped[str] = mapped_column(String(255), nullable=False)
    client_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    client_company: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Proposal Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_of_work: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[ProposalStatus] = mapped_column(
        Enum(ProposalStatus), default=ProposalStatus.DRAFT, nullable=False
    )

    # Financial
    total_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    deposit_percent: Mapped[float] = mapped_column(Float, default=25.0, nullable=False)
    deposit_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timing
    sent_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    signed_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deposit_paid_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Signature
    signature_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    signature_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Stripe
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )

    # Location / Project Link
    property_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    lead_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Job created from this proposal
    job_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # Avatar intake source
    intake_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generated_by_ai: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Proposal {self.title} ${self.total_amount_cents / 100:.2f} ({self.status.value})>"
