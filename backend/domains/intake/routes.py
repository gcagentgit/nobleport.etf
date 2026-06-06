"""
NoblePort Intake API

Endpoints for first-touch lead capture, qualification, and assignment.
"""

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.domains.intake.service import IntakeService

router = APIRouter()


@router.post("/capture", status_code=201)
async def capture(
    payload: dict[str, Any] = Body(...),
    source: str = "website",
    db: AsyncSession = Depends(get_db),
):
    """Public webhook target for inbound lead forms."""
    service = IntakeService(db)
    lead = await service.capture(source=source, payload=payload)
    return {"id": lead.id, "status": lead.status.value, "source": lead.source.value}


@router.post("/qualify/{lead_id}")
async def qualify(
    lead_id: str,
    signals: dict[str, Any] = Body(default_factory=dict),
    db: AsyncSession = Depends(get_db),
):
    service = IntakeService(db)
    try:
        result = await service.qualify(lead_id, signals)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    lead = result["lead"]
    return {
        "lead_id": lead.id,
        "score": result["score"],
        "route": result["route"],
        "status": lead.status.value,
    }


@router.post("/assign/{lead_id}")
async def assign(
    lead_id: str,
    owner: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    service = IntakeService(db)
    try:
        lead = await service.assign(lead_id, owner)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"lead_id": lead.id, "assigned_to": lead.assigned_to, "status": lead.status.value}


@router.get("/sources")
async def sources(db: AsyncSession = Depends(get_db)):
    """Count of leads captured by source over the last 30 days."""
    service = IntakeService(db)
    return {"window_days": 30, "sources": await service.sources_last_30_days()}
