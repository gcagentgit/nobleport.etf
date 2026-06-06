"""
NoblePort Follow-Ups API

Endpoints for managing sequences, instances, and the due-step queue.
"""

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.domains.follow_ups.service import FollowUpService

router = APIRouter()


def _seq_dict(seq) -> dict:
    return {
        "id": seq.id,
        "name": seq.name,
        "description": seq.description,
        "trigger_event": seq.trigger_event,
        "active": seq.active,
    }


def _inst_dict(inst) -> dict:
    return {
        "id": inst.id,
        "sequence_id": inst.sequence_id,
        "contact_id": inst.contact_id,
        "lead_id": inst.lead_id,
        "job_id": inst.job_id,
        "current_step": inst.current_step,
        "status": inst.status.value,
        "next_send_at": inst.next_send_at.isoformat() if inst.next_send_at else None,
        "started_at": inst.started_at.isoformat() if inst.started_at else None,
        "completed_at": inst.completed_at.isoformat() if inst.completed_at else None,
    }


@router.get("/sequences")
async def list_sequences(db: AsyncSession = Depends(get_db)):
    service = FollowUpService(db)
    return [_seq_dict(s) for s in await service.list_sequences()]


@router.post("/sequences", status_code=201)
async def create_sequence(
    name: str = Body(...),
    steps: list[dict[str, Any]] = Body(...),
    description: str | None = Body(None),
    trigger_event: str | None = Body(None),
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    try:
        sequence = await service.create_sequence(
            name=name,
            steps=steps,
            description=description,
            trigger_event=trigger_event,
        )
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _seq_dict(sequence)


@router.get("/instances")
async def list_instances(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    return [_inst_dict(i) for i in await service.list_instances(status=status)]


@router.post("/start", status_code=201)
async def start(
    sequence_id: str = Body(...),
    target: dict[str, str] = Body(default_factory=dict),
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    try:
        instance = await service.start_sequence(sequence_id, target)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _inst_dict(instance)


@router.post("/pause/{instance_id}")
async def pause(instance_id: str, db: AsyncSession = Depends(get_db)):
    service = FollowUpService(db)
    try:
        instance = await service.pause_instance(instance_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _inst_dict(instance)


@router.post("/cancel/{instance_id}")
async def cancel(instance_id: str, db: AsyncSession = Depends(get_db)):
    service = FollowUpService(db)
    try:
        instance = await service.cancel_instance(instance_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _inst_dict(instance)


@router.post("/respond/{instance_id}")
async def respond(
    instance_id: str,
    response: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    try:
        instance = await service.record_response(instance_id, response)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _inst_dict(instance)


@router.post("/process-due")
async def process_due(db: AsyncSession = Depends(get_db)):
    """Worker entry point — advance every instance whose next_send_at has passed."""
    service = FollowUpService(db)
    return await service.process_due()


@router.get("/due")
async def due(db: AsyncSession = Depends(get_db)):
    """All steps due in the next 24 hours."""
    service = FollowUpService(db)
    instances = await service.due_soon(hours=24)
    return {"count": len(instances), "items": [_inst_dict(i) for i in instances]}
