"""
NoblePort Agent Registry Model

Tracks all AI agents in the mesh: Stephanie.ai, GCagent.ai,
PermitStream.ai, Cyborg.ai, and all sub-agents. Provides health
monitoring, task tracking, and kill-switch state.
"""

from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class AgentFamily(str, PyEnum):
    STEPHANIE = "stephanie"
    GCAGENT = "gcagent"
    PERMITSTREAM = "permitstream"
    CYBORG = "cyborg"
    AUDIT_BEACON = "audit_beacon"
    TRUST_PIPELINE = "trust_pipeline"
    OTHER = "other"


class AgentHealth(str, PyEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class RegisteredAgent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "registered_agents"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    family: Mapped[AgentFamily] = mapped_column(
        Enum(AgentFamily), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)

    health: Mapped[AgentHealth] = mapped_column(
        Enum(AgentHealth), default=AgentHealth.UNKNOWN, nullable=False
    )

    queue_depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    in_flight: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    p95_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    uptime_30d: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_heartbeat: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    kill_switch_armed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    kill_switch_scope: Mapped[str | None] = mapped_column(String(255), nullable=True)

    current_task: Mapped[str | None] = mapped_column(String(500), nullable=True)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    capabilities_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Agent {self.name} [{self.family.value}] ({self.health.value})>"
