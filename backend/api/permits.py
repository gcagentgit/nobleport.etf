"""
PermitStream API — Permit Workflow Endpoints

Manages the permit lifecycle from intake through issuance.
Provides deficiency scoring, zoning risk assessment, and
municipal forecast intelligence.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.models.permit import Permit, PermitStatus, PermitType
from backend.services.audit_beacon import AuditBeacon
from backend.services.permit_stream import PermitStreamEngine
from backend.models.audit_entry import AuditAction, ApprovalType

router = APIRouter()


class PermitCreate(BaseModel):
    ahj: str
    property_address: str
    permit_type: str = "building"
    job_id: str | None = None
    lead_id: str | None = None
    project_description: str | None = None
    scope_type: str | None = None
    estimated_cost: float = 0.0
    square_footage: float | None = None


class PermitResponse(BaseModel):
    id: str
    internal_ref: str
    permit_number: str | None
    permit_type: str
    status: str
    ahj: str
    property_address: str
    project_description: str | None
    scope_type: str | None
    estimated_cost: float
    square_footage: float | None
    deficiency_score: float
    zoning_risk_score: float
    completeness_score: float
    forecast_days_to_issue: int | None
    deficiency_count: int
    correction_rounds: int
    submitted_at: str | None
    approved_at: str | None
    issued_at: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PermitTransition(BaseModel):
    status: str


@router.get("")
async def list_permits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    ahj: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Permit)
    if status:
        query = query.where(Permit.status == PermitStatus(status))
    if ahj:
        query = query.where(Permit.ahj == ahj)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Permit.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    permits = result.scalars().all()

    return {
        "items": [PermitResponse.model_validate(p) for p in permits],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.post("", response_model=PermitResponse)
async def create_permit(
    data: PermitCreate, db: AsyncSession = Depends(get_db)
):
    permit = await PermitStreamEngine.create_permit(
        db,
        ahj=data.ahj,
        property_address=data.property_address,
        permit_type=PermitType(data.permit_type),
        job_id=data.job_id,
        lead_id=data.lead_id,
        project_description=data.project_description,
        scope_type=data.scope_type,
        estimated_cost=data.estimated_cost,
        square_footage=data.square_footage,
    )

    await AuditBeacon.record(
        db, operator="system", action=AuditAction.CREATE,
        subject_type="permit", subject_id=permit.id,
        agent="PermitStream", subject_label=permit.internal_ref,
        detail=f"Created permit for {data.property_address} in {data.ahj}",
    )

    return PermitResponse.model_validate(permit)


@router.get("/{permit_id}", response_model=PermitResponse)
async def get_permit(permit_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Permit).where(Permit.id == permit_id))
    permit = result.scalar_one_or_none()
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")
    return PermitResponse.model_validate(permit)


@router.post("/{permit_id}/transition", response_model=PermitResponse)
async def transition_permit(
    permit_id: str,
    data: PermitTransition,
    db: AsyncSession = Depends(get_db),
):
    try:
        permit = await PermitStreamEngine.transition_status(
            permit_id, PermitStatus(data.status), db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await AuditBeacon.record(
        db, operator="system", action=AuditAction.TRANSITION,
        subject_type="permit", subject_id=permit.id,
        agent="PermitStream", subject_label=permit.internal_ref,
        approval=ApprovalType.HUMAN if data.status in ("approved", "issued") else ApprovalType.AUTO,
        detail=f"Transitioned to {data.status}",
    )

    return PermitResponse.model_validate(permit)


@router.get("/{permit_id}/deficiencies")
async def score_deficiencies(
    permit_id: str, db: AsyncSession = Depends(get_db)
):
    try:
        return await PermitStreamEngine.score_deficiencies(permit_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/forecast/{ahj}")
async def municipal_forecast(
    ahj: str, db: AsyncSession = Depends(get_db)
):
    return await PermitStreamEngine.get_municipal_forecast(ahj, db)
