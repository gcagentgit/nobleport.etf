"""
NoblePort Jobs Domain Routes

HTTP endpoints for the active-job execution lifecycle.
"""

from datetime import date as date_type
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.domains.jobs.service import JobsService
from backend.models.change_order import ChangeOrderReason
from backend.models.job import JobStatus

router = APIRouter()


class KickoffRequest(BaseModel):
    project_manager: str | None = None
    crew: str | None = None
    start_date: date_type | None = None


class ProgressRequest(BaseModel):
    percent_complete: float = Field(ge=0, le=100)


class ChangeOrderRequest(BaseModel):
    title: str
    labor_cost: float = 0.0
    material_cost: float = 0.0
    markup_percent: float = 20.0
    reason: ChangeOrderReason = ChangeOrderReason.CLIENT_REQUEST
    description: str | None = None


class FlagAtRiskRequest(BaseModel):
    reason: str


def _job_to_dict(job) -> dict[str, Any]:
    return {
        "id": job.id,
        "job_number": job.job_number,
        "status": job.status.value,
        "contract_value": job.contract_value,
        "deposit_gate_passed": job.deposit_gate_passed,
        "crew": job.crew,
        "start_date": job.start_date,
        "estimated_end_date": job.estimated_end_date,
        "actual_end_date": job.actual_end_date,
        "change_order_total": job.change_order_total,
        "change_order_count": job.change_order_count,
    }


@router.get("/active")
async def list_active_jobs(
    status: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    svc = JobsService(db)
    parsed_status = JobStatus(status) if status else None
    jobs = await svc.get_active_jobs(status=parsed_status, limit=limit)
    return {"items": [_job_to_dict(j) for j in jobs], "count": len(jobs)}


@router.get("/{job_id}/health")
async def job_health(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = JobsService(db)
    try:
        return await svc.get_health(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{job_id}/kickoff")
async def kickoff_job(
    job_id: str,
    payload: KickoffRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = JobsService(db)
    try:
        job = await svc.kickoff(
            job_id,
            project_manager=payload.project_manager,
            crew=payload.crew,
            start_date=payload.start_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _job_to_dict(job)


@router.post("/{job_id}/progress")
async def post_progress(
    job_id: str,
    payload: ProgressRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = JobsService(db)
    try:
        job = await svc.update_progress(job_id, payload.percent_complete)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _job_to_dict(job)


@router.post("/{job_id}/closeout")
async def closeout_job(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = JobsService(db)
    try:
        job = await svc.closeout(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _job_to_dict(job)


@router.get("/{job_id}/profitability")
async def get_profitability(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = JobsService(db)
    try:
        return await svc.get_profitability(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{job_id}/flag-at-risk")
async def flag_at_risk(
    job_id: str,
    payload: FlagAtRiskRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = JobsService(db)
    try:
        job = await svc.flag_at_risk(job_id, payload.reason)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _job_to_dict(job)


@router.post("/{job_id}/change-order")
async def add_change_order(
    job_id: str,
    payload: ChangeOrderRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = JobsService(db)
    try:
        co = await svc.add_change_order(
            job_id,
            title=payload.title,
            labor_cost=payload.labor_cost,
            material_cost=payload.material_cost,
            markup_percent=payload.markup_percent,
            reason=payload.reason,
            description=payload.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "id": co.id,
        "change_order_number": co.change_order_number,
        "total_amount": co.total_amount,
        "status": co.status.value,
    }


@router.get("/{job_id}/forecast")
async def get_forecast(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = JobsService(db)
    try:
        return await svc.forecast_completion(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
