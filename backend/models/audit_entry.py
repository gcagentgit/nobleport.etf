"""
NoblePort AuditBeacon Model — Immutable Audit Memory

Every operational mutation gets an immutable, hash-linked audit entry.
This is the core of the trust infrastructure: searchable, timestamped,
hash-linked, auditable, defensible.
"""

from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class AuditAction(str, PyEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    TRANSITION = "transition"
    PAYMENT = "payment"
    SIGN = "sign"
    SUBMIT = "submit"
    GATE_PASS = "gate_pass"
    GATE_BLOCK = "gate_block"
    AGENT_TASK = "agent_task"
    COMPLIANCE = "compliance"
    KILL_SWITCH = "kill_switch"


class ApprovalType(str, PyEnum):
    AUTO = "auto"
    HUMAN = "human"
    MULTI_SIG = "multi_sig"
    DAO = "dao"
    NONE = "none"


class AuditStatus(str, PyEnum):
    COMMITTED = "committed"
    PENDING = "pending"
    REJECTED = "rejected"
    ANCHORED = "anchored"


class AuditEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_entries"

    timestamp: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    operator: Mapped[str] = mapped_column(String(255), nullable=False)
    agent: Mapped[str | None] = mapped_column(String(100), nullable=True)

    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction), nullable=False, index=True
    )

    # What was acted upon
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    subject_label: Mapped[str | None] = mapped_column(String(500), nullable=True)

    approval: Mapped[ApprovalType] = mapped_column(
        Enum(ApprovalType), default=ApprovalType.AUTO, nullable=False
    )

    # Immutable hash chain
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Blockchain anchor (optional, Phase 3)
    anchor_tx: Mapped[str | None] = mapped_column(String(66), nullable=True)
    anchor_chain: Mapped[str | None] = mapped_column(String(50), nullable=True)

    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus), default=AuditStatus.COMMITTED, nullable=False
    )

    # Detail payload (JSON)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Whether this entry has been verified
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<AuditEntry {self.action.value} {self.subject_type}/{self.subject_id} by {self.operator}>"
