"""
NoblePort Change Orders API

Additional Work Orders that modify job scope and cost.
Closes the margin leak loop:
  submit → approve → auto-invoice (Stripe link) → webhook → paid → attached to job

This is where margins are won.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.models.change_order import ChangeOrder, ChangeOrderStatus
from backend.models.job import Job
from backend.services.stripe_service import StripeService

router = APIRouter()
stripe_service = StripeService()


class ChangeOrderCreate(BaseModel):
    title: str
    description: str
    reason: str | None = None
    amount_cents: int = Field(..., gt=0)
    submitted_by: str | None = None


class ChangeOrderResponse(BaseModel):
    id: str
    job_id: str
    title: str
    description: str
    reason: str | None
    status: str
    amount_cents: int
    submitted_by: str | None
    approved_by: str | None
    approved_at: datetime | None
    client_approved: bool | None
    client_approved_at: datetime | None
    stripe_checkout_session_id: str | None
    paid_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangeOrderApproval(BaseModel):
    approved_by: str
    client_approved: bool = True


@router.get("/{job_id}/change-orders")
async def list_change_orders(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChangeOrder)
        .where(ChangeOrder.job_id == job_id)
        .order_by(ChangeOrder.created_at.desc())
    )
    return [ChangeOrderResponse.model_validate(co) for co in result.scalars()]


@router.post("/{job_id}/change-orders", status_code=201)
async def create_change_order(
    job_id: str, data: ChangeOrderCreate, db: AsyncSession = Depends(get_db)
):
    """Submit a change order for a job. Starts in PENDING_APPROVAL."""
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    co = ChangeOrder(
        job_id=job_id,
        title=data.title,
        description=data.description,
        reason=data.reason,
        amount_cents=data.amount_cents,
        submitted_by=data.submitted_by,
    )
    db.add(co)
    await db.commit()
    await db.refresh(co)
    return ChangeOrderResponse.model_validate(co)


@router.post("/{job_id}/change-orders/{co_id}/approve")
async def approve_change_order(
    job_id: str,
    co_id: str,
    data: ChangeOrderApproval,
    db: AsyncSession = Depends(get_db),
):
    """
    Approve a change order.
    Automatically creates a Stripe checkout — payment closes the loop.
    approve → invoice instantly → Stripe link → webhook → attach to job
    """
    result = await db.execute(
        select(ChangeOrder).where(
            ChangeOrder.id == co_id, ChangeOrder.job_id == job_id
        )
    )
    co = result.scalar_one_or_none()
    if not co:
        raise HTTPException(status_code=404, detail="Change order not found")

    if co.status != ChangeOrderStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve change order in {co.status.value} status",
        )

    now = datetime.now(timezone.utc)
    co.status = ChangeOrderStatus.APPROVED
    co.approved_by = data.approved_by
    co.approved_at = now
    co.client_approved = data.client_approved
    co.client_approved_at = now if data.client_approved else None

    await db.commit()
    await db.refresh(co)

    # Auto-create Stripe checkout for the change order
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one()

    checkout_result = await stripe_service.create_change_order_checkout(
        change_order=co,
        job_title=job.title,
        client_email=job.client_email,
    )

    return {
        "change_order": ChangeOrderResponse.model_validate(co),
        "checkout": checkout_result,
        "message": "Change order approved. Payment checkout created.",
    }
