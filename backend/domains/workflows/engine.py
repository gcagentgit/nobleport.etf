"""
NoblePort Workflows Engine

The async execution engine for workflow templates and instances.
Resolves triggers, spawns instances, advances steps, dispatches action
handlers, and finalizes runs.

Action handlers are intentionally lightweight here — only `route_to_agent`
and `record_trust_event` actually hop into the AgentMesh / AuditBeacon.
The rest log and return success so the dispatch structure is in place
for later fleshing-out.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.workflows.models import (
    WorkflowInstance,
    WorkflowInstanceStatus,
    WorkflowStep,
    WorkflowStepAction,
    WorkflowStepExecution,
    WorkflowStepExecutionStatus,
    WorkflowStepFailureMode,
    WorkflowTemplate,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=str)


def _loads(blob: str | None) -> Any:
    if not blob:
        return {}
    try:
        return json.loads(blob)
    except (json.JSONDecodeError, TypeError):
        return {}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class WorkflowEngine:
    """
    Async workflow execution engine.

    All methods take an explicit `AsyncSession` so they compose cleanly
    with FastAPI's request-scoped session dependency.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # Template registration
    # -----------------------------------------------------------------------

    async def register_template(self, template_data: dict[str, Any]) -> WorkflowTemplate:
        """
        Validate and persist a workflow template + its steps.

        `template_data` shape:
            {
              "name": str,
              "description": str | None,
              "trigger_event": str,
              "trigger_filter": dict | None,
              "active": bool,
              "version": int,
              "created_by": str | None,
              "tags": list[str] | str | None,
              "steps": [
                {
                  "step_number": int,
                  "name": str,
                  "action_type": str,
                  "action_config": dict,
                  "depends_on_step": int | None,
                  "condition": str | None,
                  "timeout_seconds": int,
                  "retry_max": int,
                  "on_failure": str,
                },
                ...
              ],
            }
        """
        name = template_data.get("name")
        trigger_event = template_data.get("trigger_event")
        if not name or not trigger_event:
            raise ValueError("template requires 'name' and 'trigger_event'")

        steps = template_data.get("steps") or []
        if not steps:
            raise ValueError("template requires at least one step")

        tags = template_data.get("tags")
        if isinstance(tags, list):
            tags = ",".join(str(t) for t in tags)

        trigger_filter = template_data.get("trigger_filter")
        if isinstance(trigger_filter, dict):
            trigger_filter = _dumps(trigger_filter)

        template = WorkflowTemplate(
            name=name,
            description=template_data.get("description"),
            trigger_event=trigger_event,
            trigger_filter=trigger_filter,
            active=bool(template_data.get("active", True)),
            version=int(template_data.get("version", 1)),
            created_by=template_data.get("created_by"),
            tags=tags,
        )
        self.db.add(template)
        await self.db.flush()  # populate template.id

        for raw in steps:
            action_type = raw.get("action_type")
            if not action_type:
                raise ValueError("step requires 'action_type'")

            cfg = raw.get("action_config")
            if isinstance(cfg, (dict, list)):
                cfg = _dumps(cfg)

            on_failure_raw = raw.get("on_failure", WorkflowStepFailureMode.FAIL.value)

            step = WorkflowStep(
                template_id=template.id,
                step_number=int(raw["step_number"]),
                name=raw.get("name") or f"step-{raw['step_number']}",
                action_type=WorkflowStepAction(action_type),
                action_config=cfg,
                depends_on_step=raw.get("depends_on_step"),
                condition=raw.get("condition"),
                timeout_seconds=int(raw.get("timeout_seconds", 300)),
                retry_max=int(raw.get("retry_max", 0)),
                on_failure=WorkflowStepFailureMode(on_failure_raw),
            )
            self.db.add(step)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    # -----------------------------------------------------------------------
    # Trigger
    # -----------------------------------------------------------------------

    async def trigger(
        self,
        event_type: str,
        event_data: dict[str, Any] | None = None,
    ) -> list[WorkflowInstance]:
        """
        Find every active template that matches the event and spawn an
        instance for each. Returns the newly created instances.
        """
        event_data = event_data or {}

        stmt = select(WorkflowTemplate).where(
            WorkflowTemplate.trigger_event == event_type,
            WorkflowTemplate.active.is_(True),
        )
        result = await self.db.execute(stmt)
        templates = result.scalars().all()

        instances: list[WorkflowInstance] = []
        for tpl in templates:
            if not self._matches_filter(tpl.trigger_filter, event_data):
                continue
            inst = WorkflowInstance(
                template_id=tpl.id,
                trigger_data=_dumps(event_data),
                status=WorkflowInstanceStatus.PENDING,
                triggered_by=event_data.get("triggered_by") or event_data.get("actor"),
                related_entity_type=event_data.get("entity_type")
                or event_data.get("subject_type"),
                related_entity_id=event_data.get("entity_id")
                or event_data.get("subject_id"),
            )
            self.db.add(inst)
            instances.append(inst)

        await self.db.commit()
        for inst in instances:
            await self.db.refresh(inst)
        return instances

    def _matches_filter(
        self, trigger_filter: str | None, event_data: dict[str, Any]
    ) -> bool:
        """
        Conservative filter match: trigger_filter is JSON like
        {"status": "won", "value_gte": 50000}; every key must match
        the event payload. Unknown operators short-circuit to True so
        we don't silently drop events.
        """
        if not trigger_filter:
            return True
        cond = _loads(trigger_filter)
        if not isinstance(cond, dict):
            return True
        for key, expected in cond.items():
            if key.endswith("_gte"):
                actual = event_data.get(key[:-4])
                if actual is None or actual < expected:
                    return False
            elif key.endswith("_lte"):
                actual = event_data.get(key[:-4])
                if actual is None or actual > expected:
                    return False
            elif key.endswith("_in"):
                actual = event_data.get(key[:-3])
                if actual not in (expected or []):
                    return False
            else:
                if event_data.get(key) != expected:
                    return False
        return True

    # -----------------------------------------------------------------------
    # Instance lifecycle
    # -----------------------------------------------------------------------

    async def start_instance(self, instance_id: str) -> WorkflowInstance:
        """Transition a pending instance to running and execute the first step."""
        instance = await self._get_instance(instance_id)
        if instance.status not in (
            WorkflowInstanceStatus.PENDING,
            WorkflowInstanceStatus.WAITING,
        ):
            raise ValueError(
                f"cannot start instance in status '{instance.status.value}'"
            )

        instance.status = WorkflowInstanceStatus.RUNNING
        instance.started_at = instance.started_at or datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(instance)

        await self.advance_instance(instance_id)
        return instance

    async def advance_instance(self, instance_id: str) -> WorkflowInstance:
        """
        Move the instance to the next eligible step (based on dependency
        ordering and conditions). Executes that step. If no step remains,
        completes the instance.
        """
        instance = await self._get_instance(instance_id)
        if instance.status not in (WorkflowInstanceStatus.RUNNING,):
            return instance

        steps = await self._get_template_steps(instance.template_id)
        completed_step_numbers = await self._completed_step_numbers(instance.id)

        # Pick the next step whose dependency is satisfied and that hasn't run
        next_step: WorkflowStep | None = None
        for step in steps:
            if step.step_number in completed_step_numbers:
                continue
            if step.depends_on_step is not None and (
                step.depends_on_step not in completed_step_numbers
            ):
                continue
            next_step = step
            break

        if next_step is None:
            await self.complete_instance(instance.id, success=True)
            return await self._get_instance(instance.id)

        instance.current_step_number = next_step.step_number
        await self.db.commit()

        execution = WorkflowStepExecution(
            instance_id=instance.id,
            step_id=next_step.id,
            status=WorkflowStepExecutionStatus.PENDING,
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        await self.execute_step(execution.id)
        return await self._get_instance(instance.id)

    async def execute_step(self, execution_id: str) -> WorkflowStepExecution:
        """Run a single step execution, dispatching by action_type."""
        execution = await self._get_execution(execution_id)
        step = await self.db.get(WorkflowStep, execution.step_id)
        instance = await self._get_instance(execution.instance_id)

        if step is None:
            raise ValueError(f"step {execution.step_id} not found")

        context = _loads(instance.trigger_data)
        cfg = _loads(step.action_config)

        # Condition check
        if step.condition and not self._evaluate_condition(step.condition, context):
            execution.status = WorkflowStepExecutionStatus.SKIPPED
            execution.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(execution)
            return execution

        execution.status = WorkflowStepExecutionStatus.RUNNING
        execution.started_at = datetime.now(timezone.utc)
        execution.attempts += 1
        await self.db.commit()

        try:
            output = await self._dispatch_action(step.action_type, cfg, context)
            execution.status = WorkflowStepExecutionStatus.COMPLETED
            execution.output = _dumps(output)
            execution.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(execution)
        except Exception as exc:  # noqa: BLE001 — handlers may raise anything
            logger.exception(
                "workflow step failed: instance=%s step=%s action=%s",
                instance.id, step.id, step.action_type.value,
            )
            execution.error_message = str(exc)

            # Retry policy
            if execution.attempts <= step.retry_max:
                execution.status = WorkflowStepExecutionStatus.PENDING
                await self.db.commit()
                await self.db.refresh(execution)
                return await self.execute_step(execution.id)

            # Failure policy
            mode = step.on_failure
            if mode == WorkflowStepFailureMode.SKIP:
                execution.status = WorkflowStepExecutionStatus.SKIPPED
            else:
                execution.status = WorkflowStepExecutionStatus.FAILED
            execution.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(execution)

            if mode in (WorkflowStepFailureMode.FAIL, WorkflowStepFailureMode.ESCALATE):
                await self.complete_instance(instance.id, success=False)
                return execution

        return execution

    async def complete_instance(
        self, instance_id: str, success: bool
    ) -> WorkflowInstance:
        instance = await self._get_instance(instance_id)
        instance.status = (
            WorkflowInstanceStatus.COMPLETED if success
            else WorkflowInstanceStatus.FAILED
        )
        instance.completed_at = datetime.now(timezone.utc)
        if not success and not instance.error_message:
            instance.error_message = "one or more steps failed"
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def pause_instance(self, instance_id: str) -> WorkflowInstance:
        instance = await self._get_instance(instance_id)
        if instance.status != WorkflowInstanceStatus.RUNNING:
            raise ValueError(
                f"cannot pause instance in status '{instance.status.value}'"
            )
        instance.status = WorkflowInstanceStatus.WAITING
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def resume_instance(self, instance_id: str) -> WorkflowInstance:
        instance = await self._get_instance(instance_id)
        if instance.status != WorkflowInstanceStatus.WAITING:
            raise ValueError(
                f"cannot resume instance in status '{instance.status.value}'"
            )
        instance.status = WorkflowInstanceStatus.RUNNING
        await self.db.commit()
        await self.db.refresh(instance)
        await self.advance_instance(instance.id)
        return await self._get_instance(instance.id)

    async def cancel_instance(self, instance_id: str) -> WorkflowInstance:
        instance = await self._get_instance(instance_id)
        if instance.status in (
            WorkflowInstanceStatus.COMPLETED,
            WorkflowInstanceStatus.FAILED,
            WorkflowInstanceStatus.CANCELLED,
        ):
            raise ValueError(
                f"cannot cancel instance in status '{instance.status.value}'"
            )
        instance.status = WorkflowInstanceStatus.CANCELLED
        instance.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    # -----------------------------------------------------------------------
    # Queries
    # -----------------------------------------------------------------------

    async def get_running(self) -> list[WorkflowInstance]:
        stmt = select(WorkflowInstance).where(
            WorkflowInstance.status.in_(
                [WorkflowInstanceStatus.RUNNING, WorkflowInstanceStatus.WAITING]
            )
        ).order_by(WorkflowInstance.started_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_overdue(self) -> list[WorkflowInstance]:
        """
        Instances whose currently-running step has exceeded its
        timeout_seconds. We compute overdue from the step execution's
        started_at + step.timeout_seconds.
        """
        running = await self.get_running()
        if not running:
            return []

        overdue: list[WorkflowInstance] = []
        now = datetime.now(timezone.utc)
        for inst in running:
            # Find the in-flight execution for this instance
            stmt = (
                select(WorkflowStepExecution)
                .where(
                    WorkflowStepExecution.instance_id == inst.id,
                    WorkflowStepExecution.status == WorkflowStepExecutionStatus.RUNNING,
                )
                .order_by(WorkflowStepExecution.started_at.desc())
                .limit(1)
            )
            execution = (await self.db.execute(stmt)).scalar_one_or_none()
            if execution is None or execution.started_at is None:
                continue
            step = await self.db.get(WorkflowStep, execution.step_id)
            if step is None:
                continue
            deadline = execution.started_at + timedelta(seconds=step.timeout_seconds)
            if now > deadline:
                overdue.append(inst)
        return overdue

    # -----------------------------------------------------------------------
    # Action dispatcher
    # -----------------------------------------------------------------------

    async def _dispatch_action(
        self,
        action_type: WorkflowStepAction,
        config: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Route an action to its handler. Handlers return a dict that is
        persisted on the WorkflowStepExecution.output column.
        """
        match action_type:
            case WorkflowStepAction.ROUTE_TO_AGENT:
                return await self._handle_route_to_agent(config, context)
            case WorkflowStepAction.CREATE_TASK:
                return await self._handle_create_task(config, context)
            case WorkflowStepAction.SEND_COMMUNICATION:
                return await self._handle_send_communication(config, context)
            case WorkflowStepAction.UPDATE_ENTITY:
                return await self._handle_update_entity(config, context)
            case WorkflowStepAction.WAIT:
                return await self._handle_wait(config, context)
            case WorkflowStepAction.CONDITIONAL_BRANCH:
                return await self._handle_conditional_branch(config, context)
            case WorkflowStepAction.CALL_API:
                return await self._handle_call_api(config, context)
            case WorkflowStepAction.HUMAN_APPROVAL:
                return await self._handle_human_approval(config, context)
            case WorkflowStepAction.RECORD_TRUST_EVENT:
                return await self._handle_record_trust_event(config, context)
            case _:  # pragma: no cover — exhaustive over enum
                raise ValueError(f"unknown action_type: {action_type}")

    async def _handle_route_to_agent(
        self, config: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Hand off to AgentMesh.route_event."""
        # Lazy import to avoid circular dependency at module load
        from backend.agents.orchestrator import create_agent_mesh

        event_type = config.get("event_type")
        if not event_type:
            raise ValueError("route_to_agent requires action_config.event_type")
        payload = {**context, **(config.get("payload") or {})}

        mesh = create_agent_mesh()
        result = await mesh.route_event(event_type, payload)
        return {"handler": "route_to_agent", "agent_result": result}

    async def _handle_create_task(
        self, config: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        logger.info("workflows: create_task config=%s", config)
        return {
            "handler": "create_task",
            "task": config.get("task_name", "unnamed"),
            "assignee": config.get("assignee"),
            "status": "queued",
        }

    async def _handle_send_communication(
        self, config: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        logger.info("workflows: send_communication config=%s", config)
        return {
            "handler": "send_communication",
            "channel": config.get("channel", "email"),
            "template": config.get("template"),
            "status": "queued",
        }

    async def _handle_update_entity(
        self, config: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        logger.info("workflows: update_entity config=%s", config)
        return {
            "handler": "update_entity",
            "entity_type": config.get("entity_type"),
            "fields": list((config.get("fields") or {}).keys()),
            "status": "queued",
        }

    async def _handle_wait(
        self, config: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        # Real impl would persist a resume-at timestamp and let a scheduler
        # advance the instance. For now we just record intent.
        seconds = int(config.get("seconds", 0))
        logger.info("workflows: wait seconds=%s", seconds)
        return {"handler": "wait", "seconds": seconds, "status": "scheduled"}

    async def _handle_conditional_branch(
        self, config: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        expr = config.get("expression", "")
        taken = self._evaluate_condition(expr, context) if expr else True
        logger.info("workflows: conditional_branch expr=%r taken=%s", expr, taken)
        return {"handler": "conditional_branch", "expression": expr, "branch_taken": taken}

    async def _handle_call_api(
        self, config: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        logger.info("workflows: call_api config=%s", config)
        return {
            "handler": "call_api",
            "url": config.get("url"),
            "method": config.get("method", "POST"),
            "status": "queued",
        }

    async def _handle_human_approval(
        self, config: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        logger.info("workflows: human_approval config=%s", config)
        return {
            "handler": "human_approval",
            "approver": config.get("approver"),
            "reason": config.get("reason"),
            "status": "awaiting_approval",
        }

    async def _handle_record_trust_event(
        self, config: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Append a record directly to the AuditBeacon ledger."""
        # Lazy import to avoid circular dependency at module load
        from backend.agents.audit_beacon import AuditBeaconAgent

        beacon = AuditBeaconAgent()
        record = {
            "actor": config.get("actor") or context.get("actor", "workflow_engine"),
            "actor_type": config.get("actor_type", "system"),
            "action": config.get("action", "workflow_step"),
            "subject_type": config.get("subject_type")
            or context.get("subject_type", "workflow"),
            "subject_id": config.get("subject_id")
            or context.get("subject_id")
            or context.get("entity_id", ""),
            "detail": config.get("detail", ""),
            "approval_type": config.get("approval_type", "auto"),
        }
        result = await beacon.record_event(record)
        return {"handler": "record_trust_event", "trust_record": result}

    # -----------------------------------------------------------------------
    # Condition evaluator (intentionally minimal & safe)
    # -----------------------------------------------------------------------

    def _evaluate_condition(self, expr: str, context: dict[str, Any]) -> bool:
        """
        Evaluate a simple "key op value" condition string.

        Supported operators: ==, !=, >=, <=, >, <, in.
        Unknown / unparseable expressions return True (don't block).
        """
        if not expr:
            return True

        for op in ("==", "!=", ">=", "<=", ">", "<"):
            if op in expr:
                left, right = (s.strip() for s in expr.split(op, 1))
                lv = context.get(left)
                rv = self._coerce(right)
                try:
                    if op == "==":
                        return lv == rv
                    if op == "!=":
                        return lv != rv
                    if op == ">=":
                        return lv >= rv  # type: ignore[operator]
                    if op == "<=":
                        return lv <= rv  # type: ignore[operator]
                    if op == ">":
                        return lv > rv  # type: ignore[operator]
                    if op == "<":
                        return lv < rv  # type: ignore[operator]
                except TypeError:
                    return False

        if " in " in expr:
            left, right = (s.strip() for s in expr.split(" in ", 1))
            rv = self._coerce(right)
            try:
                return context.get(left) in rv  # type: ignore[operator]
            except TypeError:
                return False

        return True

    @staticmethod
    def _coerce(token: str) -> Any:
        token = token.strip()
        if token.startswith(("'", '"')) and token.endswith(("'", '"')):
            return token[1:-1]
        if token in ("true", "True"):
            return True
        if token in ("false", "False"):
            return False
        if token in ("null", "None"):
            return None
        try:
            if "." in token:
                return float(token)
            return int(token)
        except ValueError:
            return token

    # -----------------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------------

    async def _get_instance(self, instance_id: str) -> WorkflowInstance:
        instance = await self.db.get(WorkflowInstance, instance_id)
        if instance is None:
            raise ValueError(f"workflow instance {instance_id} not found")
        return instance

    async def _get_execution(self, execution_id: str) -> WorkflowStepExecution:
        execution = await self.db.get(WorkflowStepExecution, execution_id)
        if execution is None:
            raise ValueError(f"workflow step execution {execution_id} not found")
        return execution

    async def _get_template_steps(self, template_id: str) -> list[WorkflowStep]:
        stmt = (
            select(WorkflowStep)
            .where(WorkflowStep.template_id == template_id)
            .order_by(WorkflowStep.step_number.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _completed_step_numbers(self, instance_id: str) -> set[int]:
        stmt = (
            select(WorkflowStep.step_number)
            .join(
                WorkflowStepExecution,
                WorkflowStepExecution.step_id == WorkflowStep.id,
            )
            .where(
                WorkflowStepExecution.instance_id == instance_id,
                WorkflowStepExecution.status.in_(
                    [
                        WorkflowStepExecutionStatus.COMPLETED,
                        WorkflowStepExecutionStatus.SKIPPED,
                    ]
                ),
            )
        )
        result = await self.db.execute(stmt)
        return {row for row in result.scalars().all()}
