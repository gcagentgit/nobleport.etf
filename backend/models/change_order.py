"""
NoblePort Change Order Model

Additional Work Orders (AWOs) that modify job scope and cost.
Closes the margin leak loop:
  approve → auto-invoice → Stripe link → webhook → attach to job
"""

from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class ChangeOrderStatus(str, PyEnum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    INVOICED = "invoiced"
    PAID = "paid"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ChangeOrder(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "change_orders"

    job_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # Details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ChangeOrderStatus] = mapped_column(
        Enum(ChangeOrderStatus), default=ChangeOrderStatus.PENDING_APPROVAL,
        nullable=False,
    )

    # Financial
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    # Approval
    submitted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    client_approved: Mapped[bool | None] = mapped_column(nullable=True)
    client_approved_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Payment
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    paid_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ChangeOrder {self.title} ${self.amount_cents / 100:.2f} ({self.status.value})>"
