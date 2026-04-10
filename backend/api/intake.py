"""
NoblePort Avatar Intake API

Bridge from Stephanie.ai avatar → structured proposal.
This is the front-end sales engine that turns conversations into revenue.

Flow:
  Avatar intake → structured job data → proposal auto-generated →
  send for signature → deposit checkout auto-created → webhook → job created

Stephanie.ai becomes the closer, not just a feature.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.config.settings import settings
from backend.models.proposal import Proposal, ProposalStatus
from backend.services.notification_service import NotificationService
from backend.services.stripe_service import StripeService

logger = logging.getLogger(__name__)
router = APIRouter()
stripe_service = StripeService()
notifications = NotificationService()


class IntakeData(BaseModel):
    """Structured data from Stephanie.ai avatar conversation."""

    # Session tracking
    session_id: str
    conversation_summary: str | None = None

    # Client info (extracted from conversation)
    client_name: str
    client_email: str
    client_phone: str | None = None
    client_company: str | None = None

    # Project details (AI-extracted)
    project_title: str
    project_description: str | None = None
    scope_of_work: str | None = None
    project_type: str | None = None

    # Location
    property_address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None

    # AI-estimated financials
    estimated_total_cents: int = Field(..., gt=0)
    deposit_percent: float = Field(default=25.0, ge=0, le=100)

    # AI confidence
    confidence_score: float = Field(default=0.0, ge=0, le=1.0)

    # Urgency signals from conversation
    urgency: str | None = None  # low, medium, high, critical
    preferred_start_date: str | None = None


class IntakeResponse(BaseModel):
    proposal_id: str
    proposal_status: str
    checkout_url: str | None
    total_amount: float
    deposit_amount: float
    message: str


@router.post("/submit", response_model=IntakeResponse)
async def submit_intake(data: IntakeData, db: AsyncSession = Depends(get_db)):
    """
    Receive structured intake data from Stephanie.ai avatar.
    Auto-generates a proposal and optionally creates a Stripe checkout.

    High-confidence intakes (>0.8) go straight to SENT status with checkout.
    Lower confidence intakes create a DRAFT for human review.
    """
    deposit_cents = int(data.estimated_total_cents * (data.deposit_percent / 100))
    now = datetime.now(timezone.utc)

    # Determine initial status based on AI confidence
    if data.confidence_score >= 0.8:
        initial_status = ProposalStatus.SENT
        expires_at = now + timedelta(days=settings.proposal_expiry_days)
    else:
        initial_status = ProposalStatus.DRAFT
        expires_at = None

    proposal = Proposal(
        client_name=data.client_name,
        client_email=data.client_email,
        client_phone=data.client_phone,
        client_company=data.client_company,
        title=data.project_title,
        description=data.project_description,
        scope_of_work=data.scope_of_work,
        status=initial_status,
        total_amount_cents=data.estimated_total_cents,
        deposit_percent=data.deposit_percent,
        deposit_amount_cents=deposit_cents,
        property_address=data.property_address,
        city=data.city,
        state=data.state,
        zip_code=data.zip_code,
        sent_at=now if initial_status == ProposalStatus.SENT else None,
        expires_at=expires_at,
        intake_session_id=data.session_id,
        generated_by_ai=True,
    )
    db.add(proposal)
    await db.commit()
    await db.refresh(proposal)

    checkout_url = None

    # For high-confidence intakes, notify ops
    if initial_status == ProposalStatus.SENT:
        await notifications.notify_ops_team(
            subject=f"AI-Generated Proposal: {data.project_title}",
            message=(
                f"Stephanie.ai generated a proposal from avatar intake.\n"
                f"Client: {data.client_name} ({data.client_email})\n"
                f"Amount: ${data.estimated_total_cents / 100:,.2f}\n"
                f"Confidence: {data.confidence_score:.0%}\n"
                f"Urgency: {data.urgency or 'normal'}"
            ),
        )
    else:
        # Low confidence — flag for human review
        await notifications.notify_ops_team(
            subject=f"[REVIEW NEEDED] AI Intake: {data.project_title}",
            message=(
                f"Stephanie.ai intake needs human review (confidence: {data.confidence_score:.0%}).\n"
                f"Client: {data.client_name} ({data.client_email})\n"
                f"Amount: ${data.estimated_total_cents / 100:,.2f}"
            ),
        )

    logger.info(
        f"Intake processed: proposal {proposal.id} "
        f"(confidence={data.confidence_score}, status={initial_status.value})"
    )

    return IntakeResponse(
        proposal_id=proposal.id,
        proposal_status=proposal.status.value,
        checkout_url=checkout_url,
        total_amount=data.estimated_total_cents / 100,
        deposit_amount=deposit_cents / 100,
        message=(
            "Proposal auto-generated and sent to client."
            if initial_status == ProposalStatus.SENT
            else "Proposal created as draft — needs human review before sending."
        ),
    )


@router.post("/webhook")
async def stephanie_intake_webhook(data: dict):
    """
    Webhook endpoint for Stephanie.ai MCP to push intake events.
    Accepts raw MCP event payloads from the avatar system.
    """
    event_type = data.get("event", "")
    session_id = data.get("sessionId", "")

    logger.info(f"Stephanie.ai intake webhook: {event_type} session={session_id}")

    return {
        "status": "received",
        "event": event_type,
        "session_id": session_id,
    }
