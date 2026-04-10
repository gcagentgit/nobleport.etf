"""
NoblePort Proposals API

Full proposal lifecycle with deposit enforcement.
Signing a proposal auto-creates a Stripe checkout — no manual links.

Flow: create → send → sign → auto-checkout → deposit → job
"""

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.config.settings import settings
from backend.models.proposal import Proposal, ProposalStatus
from backend.services.notification_service import NotificationService
from backend.services.stripe_service import StripeService

router = APIRouter()
stripe_service = StripeService()
notifications = NotificationService()


class ProposalCreate(BaseModel):
    client_name: str
    client_email: str
    client_phone: str | None = None
    client_company: str | None = None
    title: str
    description: str | None = None
    scope_of_work: str | None = None
    total_amount_cents: int = Field(..., gt=0)
    deposit_percent: float = Field(default=25.0, ge=0, le=100)
    property_address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    lead_id: str | None = None


class ProposalResponse(BaseModel):
    id: str
    client_name: str
    client_email: str
    client_phone: str | None
    title: str
    description: str | None
    scope_of_work: str | None
    status: str
    total_amount_cents: int
    deposit_percent: float
    deposit_amount_cents: int
    sent_at: datetime | None
    signed_at: datetime | None
    expires_at: datetime | None
    deposit_paid_at: datetime | None
    stripe_checkout_session_id: str | None
    job_id: str | None
    generated_by_ai: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("")
async def list_proposals(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Proposal)
    if status:
        query = query.where(Proposal.status == ProposalStatus(status))
    query = query.order_by(Proposal.created_at.desc())
    result = await db.execute(query)
    proposals = result.scalars().all()
    return [ProposalResponse.model_validate(p) for p in proposals]


@router.get("/{proposal_id}")
async def get_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalResponse.model_validate(proposal)


@router.post("", status_code=201)
async def create_proposal(data: ProposalCreate, db: AsyncSession = Depends(get_db)):
    deposit_cents = int(data.total_amount_cents * (data.deposit_percent / 100))

    proposal = Proposal(
        client_name=data.client_name,
        client_email=data.client_email,
        client_phone=data.client_phone,
        client_company=data.client_company,
        title=data.title,
        description=data.description,
        scope_of_work=data.scope_of_work,
        total_amount_cents=data.total_amount_cents,
        deposit_percent=data.deposit_percent,
        deposit_amount_cents=deposit_cents,
        property_address=data.property_address,
        city=data.city,
        state=data.state,
        zip_code=data.zip_code,
        lead_id=data.lead_id,
    )
    db.add(proposal)
    await db.commit()
    await db.refresh(proposal)
    return ProposalResponse.model_validate(proposal)


@router.post("/{proposal_id}/send")
async def send_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    """Mark proposal as sent and set expiration date."""
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status != ProposalStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Cannot send proposal in {proposal.status.value} status")

    now = datetime.now(timezone.utc)
    proposal.status = ProposalStatus.SENT
    proposal.sent_at = now
    proposal.expires_at = now + timedelta(days=settings.proposal_expiry_days)

    await db.commit()
    await db.refresh(proposal)
    return ProposalResponse.model_validate(proposal)


@router.post("/{proposal_id}/sign")
async def sign_proposal(proposal_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Client signs proposal → status moves to DEPOSIT_PENDING.
    Auto-creates Stripe checkout session. No manual link needed.

    Signature = intent only. Job NOT created yet.
    """
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status not in (ProposalStatus.SENT, ProposalStatus.SIGNED):
        raise HTTPException(status_code=400, detail=f"Cannot sign proposal in {proposal.status.value} status")

    # Check expiration
    if proposal.expires_at and proposal.expires_at < datetime.now(timezone.utc):
        proposal.status = ProposalStatus.VOID
        await db.commit()
        raise HTTPException(status_code=410, detail="Proposal has expired")

    now = datetime.now(timezone.utc)
    client_ip = request.client.host if request.client else "unknown"
    proposal.status = ProposalStatus.SIGNED
    proposal.signed_at = now
    proposal.signature_ip = client_ip
    proposal.signature_hash = hashlib.sha256(
        f"{proposal.id}:{client_ip}:{now.isoformat()}".encode()
    ).hexdigest()

    await db.commit()
    await db.refresh(proposal)

    # Auto-create Stripe checkout for deposit
    checkout_result = None
    if settings.stripe_secret_key:
        checkout_result = await stripe_service.create_deposit_checkout(proposal)
        # Notify client
        if checkout_result.get("checkout_url"):
            await notifications.send_proposal_ready(
                client_email=proposal.client_email,
                proposal_title=proposal.title,
                checkout_url=checkout_result["checkout_url"],
            )

    return {
        "proposal": ProposalResponse.model_validate(proposal),
        "checkout": checkout_result,
        "message": "Proposal signed. Deposit checkout created.",
    }
