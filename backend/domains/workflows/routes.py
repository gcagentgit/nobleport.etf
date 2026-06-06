"""
NoblePort Workflows API

HTTP surface for the workflows engine: template CRUD, manual triggering,
instance inspection and control, health metrics, default seeding.
"""

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.domains.workflows.service import WorkflowsService

router = APIRouter()


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _template_dict(t) -> dict[str, Any]:
    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "trigger_event": t.trigger_event,
        "trigger_filter": t.trigger_filter,
        "active": t.active,
        "version": t.version,
        "created_by": t.created_by,
        "tags": t.tags,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _step_dict(s) -> dict[str, Any]:
    return {
        "id": s.id,
        "template_id": s.template_id,
        "step_number": s.step_number,
        "name": s.name,
        "action_type": s.action_type.value,
        "action_config": s.action_config,
        "depends_on_step": s.depends_on_step,
        "condition": s.condition,
        "timeout_seconds": s.timeout_seconds,
        "retry_max": s.retry_max,
        "on_failure": s.on_failure.value,
    }


def _instance_dict(i) -> dict[str, Any]:
    return {
        "id": i.id,
        "template_id": i.template_id,
        "trigger_data": i.trigger_data,
        "status": i.status.value,
        "current_step_number": i.current_step_number,
        "started_at": i.started_at.isoformat() if i.started_at else None,
        "completed_at": i.completed_at.isoformat() if i.completed_at else None,
        "error_message": i.error_message,
        "triggered_by": i.triggered_by,
        "related_entity_type": i.related_entity_type,
        "related_entity_id": i.related_entity_id,
        "created_at": i.created_at.isoformat() if i.created_at else None,
    }


def _execution_dict(e) -> dict[str, Any]:
    return {
        "id": e.id,
        "instance_id": e.instance_id,
        "step_id": e.step_id,
        "status": e.status.value,
        "started_at": e.started_at.isoformat() if e.started_at else None,
        "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        "attempts": e.attempts,
        "output": e.output,
        "error_message": e.error_message,
    }


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

@router.get("/templates")
async def list_templates(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowsService(db)
    templates = await service.list_templates(active_only=active_only)
    return {"templates": [_template_dict(t) for t in templates]}


@router.post("/templates", status_code=201)
async def create_template(
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowsService(db)
    try:
        template = await service.create_template(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _template_dict(template)


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowsService(db)
    try:
        details = await service.get_template_details(template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "template": _template_dict(details["template"]),
        "steps": [_step_dict(s) for s in details["steps"]],
    }


@router.patch("/templates/{template_id}")
async def update_template(
    template_id: str,
    updates: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowsService(db)
    try:
        template = await service.update_template(template_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _template_dict(template)


@router.post("/templates/{template_id}/deactivate")
async def deactivate_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowsService(db)
    try:
        template = await service.deactivate_template(template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _template_dict(template)


# ---------------------------------------------------------------------------
# Triggering
# ---------------------------------------------------------------------------

@router.post("/trigger")
async def trigger_workflow(
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually fire an event. Body: { event_type: str, event_data: dict }.
    """
    event_type = payload.get("event_type")
    if not event_type:
        raise HTTPException(status_code=400, detail="'event_type' is required")
    event_data = payload.get("event_data") or {}

    service = WorkflowsService(db)
    result = await service.trigger_workflow(event_type, event_data)
    return {
        "event_type": result["event_type"],
        "matched": result["matched"],
        "instances": [_instance_dict(i) for i in result["instances"]],
    }


# ---------------------------------------------------------------------------
# Instances
# ---------------------------------------------------------------------------

@router.get("/instances")
async def list_instances(
    status: str | None = Query(None),
    template_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowsService(db)
    try:
        instances = await service.list_instances(
            status=status, template_id=template_id, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"instances": [_instance_dict(i) for i in instances]}


@router.get("/instances/{instance_id}")
async def get_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowsService(db)
    try:
        bundle = await service.get_instance(instance_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "instance": _instance_dict(bundle["instance"]),
        "executions": [_execution_dict(e) for e in bundle["executions"]],
    }


@router.post("/instances/{instance_id}/pause")
async def pause_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowsService(db)
    try:
        instance = await service.pause_instance(instance_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _instance_dict(instance)


@router.post("/instances/{instance_id}/resume")
async def resume_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowsService(db)
    try:
        instance = await service.resume_instance(instance_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _instance_dict(instance)


@router.post("/instances/{instance_id}/cancel")
async def cancel_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowsService(db)
    try:
        instance = await service.cancel_instance(instance_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _instance_dict(instance)


# ---------------------------------------------------------------------------
# Health / seeding
# ---------------------------------------------------------------------------

@router.get("/health")
async def workflow_health(db: AsyncSession = Depends(get_db)):
    service = WorkflowsService(db)
    return await service.get_workflow_health()


@router.post("/seed-defaults")
async def seed_defaults(db: AsyncSession = Depends(get_db)):
    service = WorkflowsService(db)
    return await service.seed_default_templates()
