"""
Intake API — Lead Intake & Qualification

Unified intake endpoint for new construction leads.
Supports voice intake, web forms, and CRM routing.
Feeds the trust pipeline and stale lead detection.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.models.lead import Lead, LeadSource, LeadStatus
from backend.services.audit_beacon import AuditBeacon
from backend.models.audit_entry import AuditAction

router = APIRouter()


class IntakeRequest(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    source: str = "website"
    property_address: str | None = None
    city: str | None = None
    state: str | None = "MA"
    zip_code: str | None = None
    estimated_value: float | None = None
    notes: str | None = None
    assigned_to: str | None = None


class LeadResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    company: str | None
    status: str
    source: str
    estimated_value: float | None
    property_address: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    assigned_to: str | None
    notes: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


@router.post("", response_model=LeadResponse)
async def submit_intake(
    data: IntakeRequest, db: AsyncSession = Depends(get_db)
):
    lead = Lead(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        company=data.company,
        source=LeadSource(data.source),
        status=LeadStatus.NEW,
        property_address=data.property_address,
        city=data.city,
        state=data.state,
        zip_code=data.zip_code,
        estimated_value=data.estimated_value,
        notes=data.notes,
        assigned_to=data.assigned_to,
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    await AuditBeacon.record(
        db, operator="intake", action=AuditAction.CREATE,
        subject_type="lead", subject_id=lead.id,
        agent="Stephanie", subject_label=f"{lead.first_name} {lead.last_name}",
        detail=f"Intake from {data.source}: {data.property_address or 'no address'}",
    )

    return LeadResponse.model_validate(lead)


@router.get("/queue")
async def intake_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(
        Lead.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED])
    )

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Lead.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    leads = result.scalars().all()

    return {
        "items": [LeadResponse.model_validate(l) for l in leads],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stale")
async def stale_leads(
    days: int = Query(14, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(Lead).where(
        and_(
            Lead.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED]),
            Lead.updated_at < cutoff,
        )
    )

    result = await db.execute(query.order_by(Lead.updated_at.asc()))
    leads = result.scalars().all()

    return {
        "stale_count": len(leads),
        "threshold_days": days,
        "items": [LeadResponse.model_validate(l) for l in leads],
    }


@router.get("/scoreboard")
async def intake_scoreboard(db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count()).select_from(Lead))
    by_status = {}
    for status in LeadStatus:
        count = await db.execute(
            select(func.count()).select_from(Lead).where(Lead.status == status)
        )
        by_status[status.value] = count.scalar() or 0

    by_source = {}
    for source in LeadSource:
        count = await db.execute(
            select(func.count()).select_from(Lead).where(Lead.source == source)
        )
        by_source[source.value] = count.scalar() or 0

    pipeline_value = await db.execute(
        select(func.coalesce(func.sum(Lead.estimated_value), 0))
        .select_from(Lead)
        .where(Lead.status.in_([
            LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED,
            LeadStatus.PROPOSAL_SENT, LeadStatus.NEGOTIATING,
        ]))
    )

    won_value = await db.execute(
        select(func.coalesce(func.sum(Lead.estimated_value), 0))
        .select_from(Lead)
        .where(Lead.status == LeadStatus.WON)
    )

    return {
        "total_leads": total.scalar() or 0,
        "by_status": by_status,
        "by_source": by_source,
        "pipeline_value": float(pipeline_value.scalar() or 0),
        "won_value": float(won_value.scalar() or 0),
    }
