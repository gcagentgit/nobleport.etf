"""
NoblePort Workflows Models

SQLAlchemy models for the workflows engine — templates, steps,
instances (runs), and per-step executions.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class WorkflowStepAction(str, PyEnum):
    ROUTE_TO_AGENT = "route_to_agent"
    CREATE_TASK = "create_task"
    SEND_COMMUNICATION = "send_communication"
    UPDATE_ENTITY = "update_entity"
    WAIT = "wait"
    CONDITIONAL_BRANCH = "conditional_branch"
    CALL_API = "call_api"
    HUMAN_APPROVAL = "human_approval"
    RECORD_TRUST_EVENT = "record_trust_event"


class WorkflowStepFailureMode(str, PyEnum):
    FAIL = "fail"
    SKIP = "skip"
    RETRY = "retry"
    ESCALATE = "escalate"


class WorkflowInstanceStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepExecutionStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

class WorkflowTemplate(Base, UUIDMixin, TimestampMixin):
    """
    A named, versioned recipe for a business process.

    Templates are matched against incoming events by `trigger_event` and
    optional `trigger_filter` (JSON-as-text expression). Only active
    templates are eligible to spawn instances.
    """

    __tablename__ = "workflow_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Trigger
    trigger_event: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    trigger_filter: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Ownership / metadata
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<WorkflowTemplate {self.name} v{self.version} "
            f"on '{self.trigger_event}' active={self.active}>"
        )


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

class WorkflowStep(Base, UUIDMixin, TimestampMixin):
    """
    A single action in a workflow template.

    Steps are ordered by `step_number` but real execution order is
    governed by `depends_on_step` (dependency graph) and `condition`
    (skip if false). `action_config` is a JSON-as-text blob whose shape
    depends on `action_type`.
    """

    __tablename__ = "workflow_steps"

    template_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_templates.id"), nullable=False, index=True
    )

    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    action_type: Mapped[WorkflowStepAction] = mapped_column(
        Enum(WorkflowStepAction), nullable=False
    )
    action_config: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Dependency / branching
    depends_on_step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    condition: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Execution policy
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    retry_max: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    on_failure: Mapped[WorkflowStepFailureMode] = mapped_column(
        Enum(WorkflowStepFailureMode),
        default=WorkflowStepFailureMode.FAIL,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<WorkflowStep #{self.step_number} {self.name} "
            f"({self.action_type.value})>"
        )


# ---------------------------------------------------------------------------
# Instances
# ---------------------------------------------------------------------------

class WorkflowInstance(Base, UUIDMixin, TimestampMixin):
    """
    A live or completed run of a workflow template.

    Each instance is bound to a template (the recipe) and an optional
    related entity (the thing being orchestrated — a lead, a job, a permit).
    """

    __tablename__ = "workflow_instances"

    template_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_templates.id"), nullable=False, index=True
    )

    # Snapshot of the event that spawned this instance
    trigger_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle
    status: Mapped[WorkflowInstanceStatus] = mapped_column(
        Enum(WorkflowInstanceStatus),
        default=WorkflowInstanceStatus.PENDING,
        nullable=False,
        index=True,
    )
    current_step_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Provenance
    triggered_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Related entity (denormalized so we don't need polymorphic FKs)
    related_entity_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    related_entity_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<WorkflowInstance {self.id} template={self.template_id} "
            f"status={self.status.value}>"
        )


# ---------------------------------------------------------------------------
# Step executions
# ---------------------------------------------------------------------------

class WorkflowStepExecution(Base, UUIDMixin, TimestampMixin):
    """
    A single attempted execution of a step within an instance.

    Retry attempts produce additional rows so the full execution history
    is preserved.
    """

    __tablename__ = "workflow_step_executions"

    instance_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_instances.id"), nullable=False, index=True
    )
    step_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_steps.id"), nullable=False, index=True
    )

    status: Mapped[WorkflowStepExecutionStatus] = mapped_column(
        Enum(WorkflowStepExecutionStatus),
        default=WorkflowStepExecutionStatus.PENDING,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<WorkflowStepExecution {self.id} "
            f"step={self.step_id} status={self.status.value} "
            f"attempts={self.attempts}>"
        )
