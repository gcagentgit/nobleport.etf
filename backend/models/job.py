"""
NoblePort Job Model

Jobs are created when payment = commitment (deposit clears).
A Job is the operational entity that drives field production.

Flow: Proposal deposit paid → Job created → Scheduling task → Field execution
"""

from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class JobStatus(str, PyEnum):
    CREATED = "created"
    SCHEDULING = "scheduling"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    INSPECTION = "inspection"
    PUNCH_LIST = "punch_list"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class Job(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "jobs"

    # Source
    proposal_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )

    # Job Details
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_of_work: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.CREATED, nullable=False
    )

    # Client
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_email: Mapped[str] = mapped_column(String(255), nullable=False)
    client_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Financial
    contract_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    deposit_collected_cents: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    total_invoiced_cents: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    total_paid_cents: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    change_order_total_cents: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # Location
    property_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Schedule
    scheduled_start: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scheduled_end: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_start: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_end: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Assignment
    assigned_crew: Mapped[str | None] = mapped_column(String(500), nullable=True)
    project_manager: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Job {self.title} ({self.status.value})>"
