"""
NoblePort Subcontractors Domain Routes

HTTP endpoints for sub directory, bids, assignments, and payments.
"""

from datetime import date as date_type
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.domains.subcontractors.models import AssignmentStatus, BidStatus
from backend.domains.subcontractors.service import SubcontractorsService

router = APIRouter()


class SubcontractorCreatePayload(BaseModel):
    business_name: str
    trade: str
    contact_name: str | None = None
    additional_trades: str | None = None
    email: str | None = None
    phone: str | None = None
    license_number: str | None = None
    license_expires: date_type | None = None
    insurance_carrier: str | None = None
    insurance_policy_number: str | None = None
    insurance_expires: date_type | None = None
    w9_on_file: bool = False
    preferred: bool = False
    rating: float | None = None
    notes: str | None = None


class SubcontractorUpdatePayload(BaseModel):
    business_name: str | None = None
    contact_name: str | None = None
    trade: str | None = None
    additional_trades: str | None = None
    email: str | None = None
    phone: str | None = None
    license_number: str | None = None
    license_expires: date_type | None = None
    insurance_carrier: str | None = None
    insurance_policy_number: str | None = None
    insurance_expires: date_type | None = None
    w9_on_file: bool | None = None
    preferred: bool | None = None
    rating: float | None = None
    notes: str | None = None


class BidPayload(BaseModel):
    subcontractor_id: str
    job_id: str
    trade: str
    bid_amount: float
    scope_summary: str | None = None
    valid_until: date_type | None = None


class AwardBidPayload(BaseModel):
    decided_by: str | None = None


class AssignmentPayload(BaseModel):
    subcontractor_id: str
    job_id: str
    scope: str | None = None
    contract_amount: float
    start_date: date_type | None = None
    end_date: date_type | None = None


class PaymentPayload(BaseModel):
    assignment_id: str
    amount: float
    payment_method: str | None = None
    reference_number: str | None = None
    lien_waiver_received: bool = False
    paid_at: datetime | None = None


# ----- Subcontractor directory -----


@router.get("/subs")
async def list_subs(
    trade: str | None = None,
    preferred: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = SubcontractorsService(db)
    subs = await svc.list_subcontractors(trade=trade, preferred=preferred)
    return {
        "items": [SubcontractorsService.sub_to_dict(s) for s in subs],
        "count": len(subs),
    }


@router.post("/subs")
async def create_sub(
    payload: SubcontractorCreatePayload,
    db: AsyncSession = Depends(get_db),
):
    svc = SubcontractorsService(db)
    try:
        sub = await svc.add_subcontractor(**payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return SubcontractorsService.sub_to_dict(sub)


@router.get("/subs/{sub_id}")
async def get_sub(sub_id: str, db: AsyncSession = Depends(get_db)):
    svc = SubcontractorsService(db)
    try:
        sub = await svc.get_subcontractor(sub_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return SubcontractorsService.sub_to_dict(sub)


@router.patch("/subs/{sub_id}")
async def update_sub(
    sub_id: str,
    payload: SubcontractorUpdatePayload,
    db: AsyncSession = Depends(get_db),
):
    svc = SubcontractorsService(db)
    try:
        sub = await svc.update_subcontractor(
            sub_id, **payload.model_dump(exclude_none=True)
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return SubcontractorsService.sub_to_dict(sub)


@router.get("/trade/{trade}")
async def preferred_for_trade(trade: str, db: AsyncSession = Depends(get_db)):
    svc = SubcontractorsService(db)
    subs = await svc.get_preferred_subs_for_trade(trade)
    return {
        "items": [SubcontractorsService.sub_to_dict(s) for s in subs],
        "count": len(subs),
    }


@router.get("/insurance/expiring")
async def expiring_insurance(
    within_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    svc = SubcontractorsService(db)
    subs = await svc.get_expiring_insurance(within_days=within_days)
    return {
        "items": [SubcontractorsService.sub_to_dict(s) for s in subs],
        "count": len(subs),
    }


# ----- Bids -----


@router.get("/bids")
async def list_bids(
    job_id: str | None = None,
    sub_id: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = SubcontractorsService(db)
    parsed_status = BidStatus(status) if status else None
    bids = await svc.list_bids(job_id=job_id, sub_id=sub_id, status=parsed_status)
    return {
        "items": [SubcontractorsService.bid_to_dict(b) for b in bids],
        "count": len(bids),
    }


@router.post("/bids")
async def create_bid(payload: BidPayload, db: AsyncSession = Depends(get_db)):
    svc = SubcontractorsService(db)
    try:
        bid = await svc.record_bid(
            sub_id=payload.subcontractor_id,
            job_id=payload.job_id,
            trade=payload.trade,
            bid_amount=payload.bid_amount,
            scope_summary=payload.scope_summary,
            valid_until=payload.valid_until,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return SubcontractorsService.bid_to_dict(bid)


@router.post("/bids/{bid_id}/award")
async def award_bid(
    bid_id: str,
    payload: AwardBidPayload | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = SubcontractorsService(db)
    try:
        bid = await svc.award_bid(
            bid_id, decided_by=payload.decided_by if payload else None
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return SubcontractorsService.bid_to_dict(bid)


# ----- Assignments -----


@router.get("/assignments")
async def list_assignments(
    job_id: str | None = None,
    sub_id: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = SubcontractorsService(db)
    parsed_status = AssignmentStatus(status) if status else None
    assignments = await svc.list_assignments(
        job_id=job_id, sub_id=sub_id, status=parsed_status
    )
    return {
        "items": [SubcontractorsService.assignment_to_dict(a) for a in assignments],
        "count": len(assignments),
    }


@router.post("/assignments")
async def create_assignment(
    payload: AssignmentPayload,
    db: AsyncSession = Depends(get_db),
):
    svc = SubcontractorsService(db)
    try:
        a = await svc.assign_to_job(
            sub_id=payload.subcontractor_id,
            job_id=payload.job_id,
            scope=payload.scope,
            contract_amount=payload.contract_amount,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return SubcontractorsService.assignment_to_dict(a)


# ----- Payments -----


@router.post("/payments")
async def record_payment(
    payload: PaymentPayload,
    db: AsyncSession = Depends(get_db),
):
    svc = SubcontractorsService(db)
    try:
        payment = await svc.record_payment(
            assignment_id=payload.assignment_id,
            amount=payload.amount,
            payment_method=payload.payment_method,
            reference_number=payload.reference_number,
            lien_waiver_received=payload.lien_waiver_received,
            paid_at=payload.paid_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return SubcontractorsService.payment_to_dict(payment)


@router.get("/subs/{sub_id}/payments")
async def list_payments_for_sub(sub_id: str, db: AsyncSession = Depends(get_db)):
    svc = SubcontractorsService(db)
    payments = await svc.list_payments_for_sub(sub_id)
    return {
        "items": [SubcontractorsService.payment_to_dict(p) for p in payments],
        "count": len(payments),
    }
