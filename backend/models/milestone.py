"""
NoblePort Milestone Model

Structured payment milestones tied to jobs.
Each milestone triggers a Stripe payment link when due.
Automated reminders chase overdue milestones.
"""

from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class MilestoneStatus(str, PyEnum):
    UPCOMING = "upcoming"
    PENDING = "pending"  # Work done, payment due
    REMINDED = "reminded"
    OVERDUE = "overdue"
    PAID = "paid"
    WAIVED = "waived"


class Milestone(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "milestones"

    job_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # Milestone Details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[MilestoneStatus] = mapped_column(
        Enum(MilestoneStatus), default=MilestoneStatus.UPCOMING, nullable=False
    )

    # Financial
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_paid_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Dates
    due_date: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    paid_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_reminded_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reminder_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Stripe
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Milestone {self.title} ${self.amount_cents / 100:.2f} ({self.status.value})>"
