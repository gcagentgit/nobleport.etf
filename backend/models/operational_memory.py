"""
NoblePort RAOS Operational Memory Model

Active operational memory layer. Stores real-time state for jobs,
AWOs, permits, inspections, meetings, contractor tasks, payment
status, and escalation states. This is the "working memory" that
agents read and write against during operations.
"""

from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class MemoryScope(str, PyEnum):
    GLOBAL = "global"
    STEPHANIE = "stephanie"
    GCAGENT = "gcagent"
    PERMITSTREAM = "permitstream"
    CYBORG = "cyborg"
    AUDIT_BEACON = "audit_beacon"


class MemoryCategory(str, PyEnum):
    JOB_STATE = "job_state"
    PERMIT_STATE = "permit_state"
    AWO_STATE = "awo_state"
    INSPECTION = "inspection"
    MEETING = "meeting"
    CONTRACTOR_TASK = "contractor_task"
    PAYMENT_STATUS = "payment_status"
    ESCALATION = "escalation"
    CUSTOMER_PREF = "customer_pref"
    VENDOR_HISTORY = "vendor_history"
    WORKFLOW = "workflow"


class OperationalMemory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "operational_memory"

    scope: Mapped[MemoryScope] = mapped_column(
        Enum(MemoryScope), default=MemoryScope.GLOBAL, nullable=False, index=True
    )
    category: Mapped[MemoryCategory] = mapped_column(
        Enum(MemoryCategory), nullable=False, index=True
    )

    key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)

    # Reference to the source entity
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # TTL support
    expires_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Version for optimistic locking
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Agent that last wrote this memory
    written_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<OpMem [{self.scope.value}:{self.category.value}] {self.key}>"
