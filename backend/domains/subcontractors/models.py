"""
NoblePort Subcontractors Domain Models

New tables for the sub directory, bids, assignments, and payments.
"""

from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class BidStatus(str, PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class AssignmentStatus(str, PyEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    TERMINATED = "terminated"


class Subcontractor(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subcontractors"

    business_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Primary trade + free-form additional trades (comma-separated)
    trade: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    additional_trades: Mapped[str | None] = mapped_column(Text, nullable=True)

    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Licensing
    license_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    license_expires: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Insurance
    insurance_carrier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    insurance_policy_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    insurance_expires: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # Tax compliance
    w9_on_file: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Quality / preference signals
    preferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Subcontractor {self.business_name} ({self.trade})>"


class SubcontractorBid(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subcontractor_bids"

    subcontractor_id: Mapped[str] = mapped_column(
        ForeignKey("subcontractors.id"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        ForeignKey("jobs.id"), nullable=False, index=True
    )

    trade: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    bid_amount: Mapped[float] = mapped_column(Float, nullable=False)
    scope_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[BidStatus] = mapped_column(
        Enum(BidStatus), default=BidStatus.PENDING, nullable=False
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decided_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<SubcontractorBid ${self.bid_amount:,.2f} {self.trade} ({self.status.value})>"


class SubcontractorAssignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subcontractor_assignments"

    subcontractor_id: Mapped[str] = mapped_column(
        ForeignKey("subcontractors.id"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        ForeignKey("jobs.id"), nullable=False, index=True
    )

    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    contract_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus), default=AssignmentStatus.SCHEDULED, nullable=False
    )

    performance_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SubcontractorAssignment sub={self.subcontractor_id} job={self.job_id} ${self.contract_amount:,.2f}>"


class SubcontractorPayment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subcontractor_payments"

    subcontractor_id: Mapped[str] = mapped_column(
        ForeignKey("subcontractors.id"), nullable=False, index=True
    )
    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("subcontractor_assignments.id"), nullable=False, index=True
    )

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lien_waiver_received: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    def __repr__(self) -> str:
        return f"<SubcontractorPayment ${self.amount:,.2f} sub={self.subcontractor_id}>"
