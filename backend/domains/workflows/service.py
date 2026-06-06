"""
NoblePort Workflows Service

API-layer facade over the WorkflowEngine. Adds CRUD-shaped operations,
read-side projections, health metrics, and default-template seeding.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.workflows.engine import WorkflowEngine
from backend.domains.workflows.models import (
    WorkflowInstance,
    WorkflowInstanceStatus,
    WorkflowStep,
    WorkflowStepAction,
    WorkflowStepExecution,
    WorkflowStepFailureMode,
    WorkflowTemplate,
)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=str)


class WorkflowsService:
    """Service layer for the workflows engine."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = WorkflowEngine(db)

    # -----------------------------------------------------------------------
    # Templates
    # -----------------------------------------------------------------------

    async def create_template(self, template_data: dict[str, Any]) -> WorkflowTemplate:
        return await self.engine.register_template(template_data)

    async def update_template(
        self, template_id: str, updates: dict[str, Any]
    ) -> WorkflowTemplate:
        template = await self.db.get(WorkflowTemplate, template_id)
        if template is None:
            raise ValueError(f"workflow template {template_id} not found")

        allowed = {
            "name",
            "description",
            "trigger_event",
            "trigger_filter",
            "active",
            "version",
            "tags",
        }
        for key, value in updates.items():
            if key not in allowed:
                continue
            if key == "trigger_filter" and isinstance(value, (dict, list)):
                value = _dumps(value)
            if key == "tags" and isinstance(value, list):
                value = ",".join(str(t) for t in value)
            setattr(template, key, value)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def deactivate_template(self, template_id: str) -> WorkflowTemplate:
        return await self.update_template(template_id, {"active": False})

    async def list_templates(
        self, active_only: bool = True
    ) -> list[WorkflowTemplate]:
        stmt = select(WorkflowTemplate)
        if active_only:
            stmt = stmt.where(WorkflowTemplate.active.is_(True))
        stmt = stmt.order_by(WorkflowTemplate.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_template_details(
        self, template_id: str
    ) -> dict[str, Any]:
        template = await self.db.get(WorkflowTemplate, template_id)
        if template is None:
            raise ValueError(f"workflow template {template_id} not found")

        steps_stmt = (
            select(WorkflowStep)
            .where(WorkflowStep.template_id == template_id)
            .order_by(WorkflowStep.step_number.asc())
        )
        steps = (await self.db.execute(steps_stmt)).scalars().all()
        return {"template": template, "steps": list(steps)}

    # -----------------------------------------------------------------------
    # Triggering & instances
    # -----------------------------------------------------------------------

    async def trigger_workflow(
        self, event_type: str, event_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Spawn instances for all matching templates and immediately start them."""
        instances = await self.engine.trigger(event_type, event_data or {})
        started: list[WorkflowInstance] = []
        for inst in instances:
            started.append(await self.engine.start_instance(inst.id))
        return {
            "event_type": event_type,
            "matched": len(instances),
            "instances": started,
        }

    async def get_instance(self, instance_id: str) -> dict[str, Any]:
        instance = await self.db.get(WorkflowInstance, instance_id)
        if instance is None:
            raise ValueError(f"workflow instance {instance_id} not found")

        exec_stmt = (
            select(WorkflowStepExecution)
            .where(WorkflowStepExecution.instance_id == instance_id)
            .order_by(WorkflowStepExecution.created_at.asc())
        )
        executions = (await self.db.execute(exec_stmt)).scalars().all()
        return {"instance": instance, "executions": list(executions)}

    async def list_instances(
        self,
        status: str | None = None,
        template_id: str | None = None,
        limit: int = 50,
    ) -> list[WorkflowInstance]:
        stmt = select(WorkflowInstance)
        if status:
            stmt = stmt.where(
                WorkflowInstance.status == WorkflowInstanceStatus(status)
            )
        if template_id:
            stmt = stmt.where(WorkflowInstance.template_id == template_id)
        stmt = stmt.order_by(WorkflowInstance.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_running_instances(self) -> list[WorkflowInstance]:
        return await self.engine.get_running()

    async def pause_instance(self, instance_id: str) -> WorkflowInstance:
        return await self.engine.pause_instance(instance_id)

    async def resume_instance(self, instance_id: str) -> WorkflowInstance:
        return await self.engine.resume_instance(instance_id)

    async def cancel_instance(self, instance_id: str) -> WorkflowInstance:
        return await self.engine.cancel_instance(instance_id)

    # -----------------------------------------------------------------------
    # Health
    # -----------------------------------------------------------------------

    async def get_workflow_health(self) -> dict[str, Any]:
        """
        Aggregate run-state metrics over the last 24h plus current
        running/waiting counts and an overall success-rate.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        async def _count(status: WorkflowInstanceStatus, recent: bool) -> int:
            stmt = (
                select(func.count())
                .select_from(WorkflowInstance)
                .where(WorkflowInstance.status == status)
            )
            if recent:
                stmt = stmt.where(WorkflowInstance.created_at >= since)
            return (await self.db.execute(stmt)).scalar_one()

        running_now = await _count(WorkflowInstanceStatus.RUNNING, recent=False)
        waiting_now = await _count(WorkflowInstanceStatus.WAITING, recent=False)
        completed_24h = await _count(WorkflowInstanceStatus.COMPLETED, recent=True)
        failed_24h = await _count(WorkflowInstanceStatus.FAILED, recent=True)
        cancelled_24h = await _count(WorkflowInstanceStatus.CANCELLED, recent=True)

        # p50 duration over last 24h completed instances
        dur_stmt = select(
            WorkflowInstance.started_at, WorkflowInstance.completed_at
        ).where(
            WorkflowInstance.status == WorkflowInstanceStatus.COMPLETED,
            WorkflowInstance.completed_at >= since,
            WorkflowInstance.started_at.is_not(None),
        )
        rows = (await self.db.execute(dur_stmt)).all()
        durations = [
            (c - s).total_seconds()
            for s, c in rows
            if s is not None and c is not None
        ]
        p50_duration_seconds = (
            round(statistics.median(durations), 2) if durations else 0.0
        )

        total_finished_24h = completed_24h + failed_24h
        success_rate = (
            round(completed_24h / total_finished_24h, 4)
            if total_finished_24h > 0
            else 1.0
        )

        overdue = await self.engine.get_overdue()

        return {
            "running_now": running_now,
            "waiting_now": waiting_now,
            "completed_24h": completed_24h,
            "failed_24h": failed_24h,
            "cancelled_24h": cancelled_24h,
            "p50_duration_seconds": p50_duration_seconds,
            "success_rate_24h": success_rate,
            "overdue_count": len(overdue),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # -----------------------------------------------------------------------
    # Canonical templates
    # -----------------------------------------------------------------------

    async def seed_default_templates(self) -> dict[str, Any]:
        """
        Register the canonical NoblePort workflows. Idempotent: skips any
        template whose `name` already exists.
        """
        existing_stmt = select(WorkflowTemplate.name)
        existing_names = {
            n for n in (await self.db.execute(existing_stmt)).scalars().all()
        }

        created: list[str] = []
        skipped: list[str] = []

        for tpl in _DEFAULT_TEMPLATES:
            if tpl["name"] in existing_names:
                skipped.append(tpl["name"])
                continue
            await self.engine.register_template(tpl)
            created.append(tpl["name"])

        return {"created": created, "skipped": skipped, "total": len(_DEFAULT_TEMPLATES)}


# ---------------------------------------------------------------------------
# Canonical workflow templates
# ---------------------------------------------------------------------------

_DEFAULT_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "Lead Intake to Estimate",
        "description": (
            "Qualify a new lead and route it into the estimating queue when "
            "signals look strong."
        ),
        "trigger_event": "lead_created",
        "active": True,
        "version": 1,
        "created_by": "system",
        "tags": ["intake", "revenue"],
        "steps": [
            {
                "step_number": 1,
                "name": "Route to Stephanie for qualification",
                "action_type": WorkflowStepAction.ROUTE_TO_AGENT.value,
                "action_config": {"event_type": "route_intake"},
                "timeout_seconds": 120,
                "retry_max": 1,
                "on_failure": WorkflowStepFailureMode.ESCALATE.value,
            },
            {
                "step_number": 2,
                "name": "Create estimator assignment task",
                "action_type": WorkflowStepAction.CREATE_TASK.value,
                "action_config": {
                    "task_name": "Build estimate",
                    "assignee": "estimator_pool",
                },
                "depends_on_step": 1,
            },
            {
                "step_number": 3,
                "name": "Notify customer that estimate is in progress",
                "action_type": WorkflowStepAction.SEND_COMMUNICATION.value,
                "action_config": {
                    "channel": "email",
                    "template": "intake_estimate_in_progress",
                },
                "depends_on_step": 2,
            },
            {
                "step_number": 4,
                "name": "Record intake_completed trust event",
                "action_type": WorkflowStepAction.RECORD_TRUST_EVENT.value,
                "action_config": {
                    "action": "intake_completed",
                    "subject_type": "lead",
                    "approval_type": "auto",
                    "detail": "Lead routed from intake to estimating.",
                },
                "depends_on_step": 3,
            },
        ],
    },
    {
        "name": "Deposit to Permit Submission",
        "description": (
            "Once the deposit clears the gate, kick off permit prep and "
            "submission with PermitStream."
        ),
        "trigger_event": "deposit_paid",
        "active": True,
        "version": 1,
        "created_by": "system",
        "tags": ["revenue", "permits"],
        "steps": [
            {
                "step_number": 1,
                "name": "Update job to permit-pending status",
                "action_type": WorkflowStepAction.UPDATE_ENTITY.value,
                "action_config": {
                    "entity_type": "job",
                    "fields": {"permit_status": "preparing"},
                },
            },
            {
                "step_number": 2,
                "name": "Route to PermitStream to prepare submission",
                "action_type": WorkflowStepAction.ROUTE_TO_AGENT.value,
                "action_config": {"event_type": "permit_submitted"},
                "depends_on_step": 1,
                "timeout_seconds": 600,
                "retry_max": 2,
            },
            {
                "step_number": 3,
                "name": "Record deposit_to_permit trust event",
                "action_type": WorkflowStepAction.RECORD_TRUST_EVENT.value,
                "action_config": {
                    "action": "deposit_to_permit_submitted",
                    "subject_type": "job",
                    "approval_type": "auto",
                },
                "depends_on_step": 2,
            },
        ],
    },
    {
        "name": "Permit Approved to Build Kickoff",
        "description": (
            "Permit issued — confirm crew, materials, and schedule, then "
            "transition the job to scheduled."
        ),
        "trigger_event": "permit_status_changed",
        "trigger_filter": {"new_status": "approved"},
        "active": True,
        "version": 1,
        "created_by": "system",
        "tags": ["permits", "construction"],
        "steps": [
            {
                "step_number": 1,
                "name": "Route to GCagent to assess job readiness",
                "action_type": WorkflowStepAction.ROUTE_TO_AGENT.value,
                "action_config": {"event_type": "assess_job_health"},
            },
            {
                "step_number": 2,
                "name": "Schedule kickoff",
                "action_type": WorkflowStepAction.CREATE_TASK.value,
                "action_config": {
                    "task_name": "Schedule build kickoff",
                    "assignee": "operations",
                },
                "depends_on_step": 1,
            },
            {
                "step_number": 3,
                "name": "Notify customer that build is scheduled",
                "action_type": WorkflowStepAction.SEND_COMMUNICATION.value,
                "action_config": {
                    "channel": "email",
                    "template": "build_kickoff_scheduled",
                },
                "depends_on_step": 2,
            },
            {
                "step_number": 4,
                "name": "Record build_kickoff trust event",
                "action_type": WorkflowStepAction.RECORD_TRUST_EVENT.value,
                "action_config": {
                    "action": "build_kickoff_scheduled",
                    "subject_type": "job",
                    "approval_type": "auto",
                },
                "depends_on_step": 3,
            },
        ],
    },
    {
        "name": "Job Completion to Maintenance Renewal Reminder",
        "description": (
            "On job completion, queue a follow-up cadence and schedule a "
            "12-month maintenance renewal reminder."
        ),
        "trigger_event": "job_completed",
        "active": True,
        "version": 1,
        "created_by": "system",
        "tags": ["revenue", "retention"],
        "steps": [
            {
                "step_number": 1,
                "name": "Send completion thank-you",
                "action_type": WorkflowStepAction.SEND_COMMUNICATION.value,
                "action_config": {
                    "channel": "email",
                    "template": "job_completion_thank_you",
                },
            },
            {
                "step_number": 2,
                "name": "Record job_completed trust event",
                "action_type": WorkflowStepAction.RECORD_TRUST_EVENT.value,
                "action_config": {
                    "action": "job_completed",
                    "subject_type": "job",
                    "approval_type": "auto",
                },
                "depends_on_step": 1,
            },
            {
                "step_number": 3,
                "name": "Wait 12 months",
                "action_type": WorkflowStepAction.WAIT.value,
                "action_config": {"seconds": 60 * 60 * 24 * 365},
                "depends_on_step": 2,
            },
            {
                "step_number": 4,
                "name": "Send maintenance renewal reminder",
                "action_type": WorkflowStepAction.SEND_COMMUNICATION.value,
                "action_config": {
                    "channel": "email",
                    "template": "maintenance_renewal_reminder",
                },
                "depends_on_step": 3,
            },
        ],
    },
]
