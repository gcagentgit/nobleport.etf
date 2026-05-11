from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.models.investor import Investor, InvestorStatus
from backend.services.encryption import decrypt
from backend.services.investor_verification import (
    InvalidTransitionError,
    validate_transition,
)

router = APIRouter()


class InvestorSummary(BaseModel):
    id: str
    email_hash: str
    accreditation_type: str
    status: InvestorStatus
    created_at: str
    intake_ip: str | None


class InvestorDetail(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str | None
    accreditation_type: str
    status: InvestorStatus
    intake_ip: str | None
    admin_notes: str | None
    verification_provider_id: str | None
    created_at: str
    updated_at: str


class InvestorListResponse(BaseModel):
    investors: list[InvestorSummary]
    total: int
    page: int
    page_size: int


class StatusPatchRequest(BaseModel):
    status: InvestorStatus
    admin_notes: str | None = None


@router.get("/investors", response_model=InvestorListResponse)
async def list_investors(
    status: InvestorStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Investor)
    count_query = select(func.count()).select_from(Investor)

    if status:
        query = query.where(Investor.status == status)
        count_query = count_query.where(Investor.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Investor.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    investors = result.scalars().all()

    return InvestorListResponse(
        investors=[
            InvestorSummary(
                id=inv.id,
                email_hash=inv.email_hash,
                accreditation_type=inv.accreditation_type.value,
                status=inv.status,
                created_at=inv.created_at.isoformat(),
                intake_ip=inv.intake_ip,
            )
            for inv in investors
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/investors/{investor_id}", response_model=InvestorDetail)
async def get_investor(
    investor_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Investor).where(Investor.id == investor_id)
    )
    investor = result.scalar_one_or_none()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    return InvestorDetail(
        id=investor.id,
        full_name=decrypt(investor.encrypted_name),
        email=decrypt(investor.encrypted_email),
        phone=decrypt(investor.encrypted_phone) if investor.encrypted_phone else None,
        accreditation_type=investor.accreditation_type.value,
        status=investor.status,
        intake_ip=investor.intake_ip,
        admin_notes=investor.admin_notes,
        verification_provider_id=investor.verification_provider_id,
        created_at=investor.created_at.isoformat(),
        updated_at=investor.updated_at.isoformat(),
    )


@router.patch("/investors/{investor_id}", response_model=InvestorDetail)
async def patch_investor_status(
    investor_id: str,
    body: StatusPatchRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Investor).where(Investor.id == investor_id)
    )
    investor = result.scalar_one_or_none()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    try:
        validate_transition(investor.status, body.status)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))

    investor.status = body.status
    if body.admin_notes is not None:
        investor.admin_notes = body.admin_notes
    if body.status == InvestorStatus.VERIFIED:
        investor.verified_at = datetime.now(timezone.utc).isoformat()

    await db.commit()
    await db.refresh(investor)

    return InvestorDetail(
        id=investor.id,
        full_name=decrypt(investor.encrypted_name),
        email=decrypt(investor.encrypted_email),
        phone=decrypt(investor.encrypted_phone) if investor.encrypted_phone else None,
        accreditation_type=investor.accreditation_type.value,
        status=investor.status,
        intake_ip=investor.intake_ip,
        admin_notes=investor.admin_notes,
        verification_provider_id=investor.verification_provider_id,
        created_at=investor.created_at.isoformat(),
        updated_at=investor.updated_at.isoformat(),
    )
