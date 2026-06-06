"""
NoblePort Leads Pipeline API

Endpoints for managing the qualified-lead pipeline.
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.domains.leads.service import LeadsService

router = APIRouter()


def _lead_dict(lead) -> dict:
    return {
        "id": lead.id,
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "email": lead.email,
        "phone": lead.phone,
        "status": lead.status.value,
        "source": lead.source.value,
        "estimated_value": lead.estimated_value,
        "assigned_to": lead.assigned_to,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


@router.get("/pipeline")
async def pipeline(
    owner: str | None = None,
    stage: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    service = LeadsService(db)
    leads = await service.get_pipeline(owner=owner, stage=stage, limit=limit)
    return {"count": len(leads), "items": [_lead_dict(lead) for lead in leads]}


@router.post("/score/{lead_id}")
async def score(lead_id: str, db: AsyncSession = Depends(get_db)):
    service = LeadsService(db)
    try:
        return await service.score(lead_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/advance/{lead_id}")
async def advance(
    lead_id: str,
    to_stage: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    service = LeadsService(db)
    try:
        lead = await service.advance_stage(lead_id, to_stage)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _lead_dict(lead)


@router.post("/reassign/{lead_id}")
async def reassign(
    lead_id: str,
    new_owner: str = Body(...),
    reason: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = LeadsService(db)
    try:
        lead = await service.reassign(lead_id, new_owner, reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _lead_dict(lead)


@router.post("/archive/{lead_id}")
async def archive(
    lead_id: str,
    reason: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    service = LeadsService(db)
    try:
        lead = await service.archive(lead_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _lead_dict(lead)


@router.get("/funnel")
async def funnel(db: AsyncSession = Depends(get_db)):
    service = LeadsService(db)
    return await service.get_funnel_snapshot()
