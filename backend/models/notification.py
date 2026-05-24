"""
NoblePort Notification Model

Tracks all system notifications across channels:
in-app, email, SMS, voice, webhook. Supports routing
to specific operators and agent escalation.
"""

from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class NotificationChannel(str, PyEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    VOICE = "voice"
    WEBHOOK = "webhook"
    SLACK = "slack"


class NotificationPriority(str, PyEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationCategory(str, PyEnum):
    LEAD = "lead"
    ESTIMATE = "estimate"
    JOB = "job"
    PERMIT = "permit"
    PAYMENT = "payment"
    COMPLIANCE = "compliance"
    AGENT = "agent"
    SYSTEM = "system"
    ESCALATION = "escalation"


class Notification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notifications"

    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel), nullable=False, index=True
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False
    )
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory), nullable=False, index=True
    )

    recipient: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    agent: Mapped[str | None] = mapped_column(String(100), nullable=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reference to the triggering entity
    subject_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subject_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    delivered_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Notification [{self.priority.value}] {self.title[:40]} -> {self.recipient}>"
