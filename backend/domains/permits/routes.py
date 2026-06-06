"""
NoblePort Permits Domain Routes

HTTP endpoints for permit applications, corrections, issuance, and inspections.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.domains.permits.service import PermitsService
from backend.models.permit import PermitType

router = APIRouter()


class SubmitPermitPayload(BaseModel):
    job_id: str
    permit_type: PermitType
    ahj: str
    reviewer: str | None = None
    estimated_review_days: int | None = None
    fee_amount: float | None = None
    notes: str | None = None


class CorrectionPayload(BaseModel):
    correction: str


class IssuancePayload(BaseModel):
    permit_number: str
    issued_at: datetime | None = None
    expires_at: datetime | None = None


class InspectionSchedulePayload(BaseModel):
    inspection_type: str
    scheduled_at: datetime
    inspector: str | None = None


class InspectionResultPayload(BaseModel):
    passed: bool
    notes: str | None = None
    corrections_required: str | None = None


@router.get("/open")
async def list_open_permits(
    ahj: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = PermitsService(db)
    permits = await svc.get_open_permits(ahj=ahj)
    return {
        "items": [PermitsService.permit_to_dict(p) for p in permits],
        "count": len(permits),
    }


@router.post("/submit")
async def submit_permit(
    payload: SubmitPermitPayload,
    db: AsyncSession = Depends(get_db),
):
    svc = PermitsService(db)
    try:
        permit = await svc.submit_permit(
            job_id=payload.job_id,
            permit_type=payload.permit_type,
            ahj=payload.ahj,
            reviewer=payload.reviewer,
            estimated_review_days=payload.estimated_review_days,
            fee_amount=payload.fee_amount,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return PermitsService.permit_to_dict(permit)


@router.post("/{permit_id}/correction")
async def record_correction(
    permit_id: str,
    payload: CorrectionPayload,
    db: AsyncSession = Depends(get_db),
):
    svc = PermitsService(db)
    try:
        permit = await svc.record_correction(permit_id, payload.correction)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return PermitsService.permit_to_dict(permit)


@router.post("/{permit_id}/issued")
async def record_issuance(
    permit_id: str,
    payload: IssuancePayload,
    db: AsyncSession = Depends(get_db),
):
    svc = PermitsService(db)
    try:
        permit = await svc.record_issuance(
            permit_id,
            payload.permit_number,
            issued_at=payload.issued_at,
            expires_at=payload.expires_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return PermitsService.permit_to_dict(permit)


@router.get("/{permit_id}")
async def get_permit(permit_id: str, db: AsyncSession = Depends(get_db)):
    svc = PermitsService(db)
    try:
        permit = await svc.get_permit(permit_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return PermitsService.permit_to_dict(permit)


@router.post("/{permit_id}/inspection")
async def schedule_inspection(
    permit_id: str,
    payload: InspectionSchedulePayload,
    db: AsyncSession = Depends(get_db),
):
    svc = PermitsService(db)
    try:
        inspection = await svc.schedule_inspection(
            permit_id,
            inspection_type=payload.inspection_type,
            scheduled_at=payload.scheduled_at,
            inspector=payload.inspector,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return PermitsService.inspection_to_dict(inspection)


@router.post("/inspections/{inspection_id}/result")
async def record_inspection_result(
    inspection_id: str,
    payload: InspectionResultPayload,
    db: AsyncSession = Depends(get_db),
):
    svc = PermitsService(db)
    try:
        inspection = await svc.record_inspection_result(
            inspection_id,
            passed=payload.passed,
            notes=payload.notes,
            corrections_required=payload.corrections_required,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return PermitsService.inspection_to_dict(inspection)


@router.get("/inspections/upcoming")
async def upcoming_inspections(
    window_days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    svc = PermitsService(db)
    inspections = await svc.get_pending_inspections(window_days=window_days)
    return {
        "items": [PermitsService.inspection_to_dict(i) for i in inspections],
        "count": len(inspections),
    }


@router.get("/by-ahj/{ahj}")
async def permits_by_ahj(ahj: str, db: AsyncSession = Depends(get_db)):
    svc = PermitsService(db)
    permits = await svc.get_permits_by_ahj(ahj)
    return {
        "items": [PermitsService.permit_to_dict(p) for p in permits],
        "count": len(permits),
    }
