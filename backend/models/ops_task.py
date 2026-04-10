"""
NoblePort Ops Task Model

Internal operations tasks auto-created by the system.
Scheduling triggers, follow-ups, and ops team notifications.
"""

from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class OpsTaskType(str, PyEnum):
    SCHEDULE_SITE_VISIT = "schedule_site_visit"
    ASSIGN_CREW = "assign_crew"
    ORDER_MATERIALS = "order_materials"
    CONFIRM_START_DATE = "confirm_start_date"
    FOLLOW_UP_CLIENT = "follow_up_client"
    COLLECT_PAYMENT = "collect_payment"
    INSPECTION_NEEDED = "inspection_needed"
    CHANGE_ORDER_REVIEW = "change_order_review"
    CLOSE_OUT_JOB = "close_out_job"


class OpsTaskStatus(str, PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OpsTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ops_tasks"

    job_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    task_type: Mapped[OpsTaskType] = mapped_column(
        Enum(OpsTaskType), nullable=False
    )
    status: Mapped[OpsTaskStatus] = mapped_column(
        Enum(OpsTaskStatus), default=OpsTaskStatus.OPEN, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<OpsTask {self.task_type.value} ({self.status.value})>"


class WebhookEvent(Base, UUIDMixin, TimestampMixin):
    """Idempotency tracking for Stripe webhooks."""
    __tablename__ = "webhook_events"

    stripe_event_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="processed", nullable=False
    )
    payload_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<WebhookEvent {self.stripe_event_id} ({self.event_type})>"
