"""
NoblePort Follow-Ups Models

Sequences, steps, and running instances for automated follow-ups.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class FollowUpChannel(str, PyEnum):
    EMAIL = "email"
    SMS = "sms"
    CALL = "call"
    TASK = "task"


class FollowUpInstanceStatus(str, PyEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class FollowUpSequence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "follow_up_sequences"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_event: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<FollowUpSequence {self.name}>"


class FollowUpStep(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "follow_up_steps"

    sequence_id: Mapped[str] = mapped_column(
        ForeignKey("follow_up_sequences.id"), nullable=False, index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    channel: Mapped[FollowUpChannel] = mapped_column(
        Enum(FollowUpChannel), nullable=False
    )
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<FollowUpStep #{self.step_number} {self.channel.value}>"


class FollowUpInstance(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "follow_up_instances"

    sequence_id: Mapped[str] = mapped_column(
        ForeignKey("follow_up_sequences.id"), nullable=False, index=True
    )
    contact_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    lead_id: Mapped[str | None] = mapped_column(
        ForeignKey("leads.id"), nullable=True, index=True
    )
    job_id: Mapped[str | None] = mapped_column(
        ForeignKey("jobs.id"), nullable=True, index=True
    )

    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[FollowUpInstanceStatus] = mapped_column(
        Enum(FollowUpInstanceStatus),
        default=FollowUpInstanceStatus.ACTIVE,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_send_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    last_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<FollowUpInstance seq={self.sequence_id} step={self.current_step} {self.status.value}>"
