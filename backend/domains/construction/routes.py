"""
NoblePort Construction Domain Routes

HTTP endpoints for field operations.
"""

from datetime import date as date_type
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.domains.construction.service import ConstructionService

router = APIRouter()


class DailyLogPayload(BaseModel):
    author: str
    log_date: date_type | None = None
    weather: str | None = None
    temperature_high_f: float | None = None
    temperature_low_f: float | None = None
    weather_delay_hours: float = 0.0
    crew_count: int = 0
    subcontractors_on_site: str | None = None
    total_man_hours: float = 0.0
    work_performed: str | None = None
    materials_received: str | None = None
    equipment_used: str | None = None
    safety_incidents: str | None = None
    safety_meeting_held: bool | None = None
    osha_notes: str | None = None
    visitors: str | None = None
    inspections_conducted: str | None = None
    notes: str | None = None
    issues: str | None = None
    delays: str | None = None


class MaterialDeliveryPayload(BaseModel):
    materials: str
    received_by: str | None = None


class SafetyIncidentPayload(BaseModel):
    details: str
    reported_by: str | None = None
    critical: bool = False


def _log_to_dict(log) -> dict[str, Any]:
    return {
        "id": log.id,
        "project_id": log.project_id,
        "log_date": log.log_date,
        "author": log.author,
        "weather": log.weather.value if log.weather else None,
        "crew_count": log.crew_count,
        "work_performed": log.work_performed,
        "materials_received": log.materials_received,
        "safety_incidents": log.safety_incidents,
    }


@router.post("/daily-log/{job_id}")
async def submit_daily_log(
    job_id: str,
    payload: DailyLogPayload,
    db: AsyncSession = Depends(get_db),
):
    svc = ConstructionService(db)
    try:
        log = await svc.submit_daily_log(job_id, payload.model_dump(exclude_none=False))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _log_to_dict(log)


@router.get("/field-status/{job_id}")
async def get_field_status(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = ConstructionService(db)
    try:
        return await svc.get_field_status(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/material-delivery/{job_id}")
async def record_material_delivery(
    job_id: str,
    payload: MaterialDeliveryPayload,
    db: AsyncSession = Depends(get_db),
):
    svc = ConstructionService(db)
    try:
        log = await svc.record_material_delivery(
            job_id, payload.materials, payload.received_by
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _log_to_dict(log)


@router.post("/safety-incident/{job_id}")
async def report_safety_incident(
    job_id: str,
    payload: SafetyIncidentPayload,
    db: AsyncSession = Depends(get_db),
):
    svc = ConstructionService(db)
    try:
        log = await svc.report_safety_incident(
            job_id,
            payload.details,
            reported_by=payload.reported_by,
            critical=payload.critical,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _log_to_dict(log)


@router.get("/today/active-sites")
async def today_active_sites(db: AsyncSession = Depends(get_db)):
    svc = ConstructionService(db)
    sites = await svc.get_today_active_sites()
    return {"items": sites, "count": len(sites)}


@router.get("/crew/locations")
async def crew_locations(db: AsyncSession = Depends(get_db)):
    svc = ConstructionService(db)
    locations = await svc.get_crew_locations()
    return {"items": locations, "count": len(locations)}
