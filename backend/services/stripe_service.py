"""
NoblePort Stripe Service

Handles all Stripe payment operations:
- Checkout session creation for deposits, milestones, and change orders
- Webhook processing with idempotency
- Payment status tracking

Principle: Payment = commitment. No manual links. Instant checkout creation.
"""

import logging
from typing import Any

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import async_session
from backend.config.settings import settings
from backend.models.change_order import ChangeOrder, ChangeOrderStatus
from backend.models.milestone import Milestone, MilestoneStatus
from backend.models.ops_task import WebhookEvent
from backend.models.proposal import Proposal, ProposalStatus

logger = logging.getLogger(__name__)


class StripeService:
    def __init__(self):
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key

    async def create_deposit_checkout(
        self, proposal: Proposal
    ) -> dict[str, Any]:
        """
        Create a Stripe Checkout Session for a proposal deposit.
        Auto-generated when proposal is signed — no manual link sending.
        """
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Deposit for {proposal.title}",
                            "description": (
                                f"Deposit ({proposal.deposit_percent}%) for "
                                f"{proposal.title} - {proposal.client_name}"
                            ),
                        },
                        "unit_amount": proposal.deposit_amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "proposal_id": proposal.id,
                "payment_kind": "deposit",
                "client_email": proposal.client_email,
            },
            customer_email=proposal.client_email,
            success_url=settings.stripe_success_url,
            cancel_url=settings.stripe_cancel_url.format(proposal_id=proposal.id),
        )

        # Store the checkout session ID on the proposal
        async with async_session() as db:
            result = await db.execute(
                select(Proposal).where(Proposal.id == proposal.id)
            )
            p = result.scalar_one()
            p.stripe_checkout_session_id = session.id
            p.status = ProposalStatus.DEPOSIT_PENDING
            await db.commit()

        logger.info(
            f"Deposit checkout created for proposal {proposal.id}: {session.id}"
        )

        return {
            "checkout_session_id": session.id,
            "checkout_url": session.url,
            "amount_cents": proposal.deposit_amount_cents,
            "proposal_id": proposal.id,
        }

    async def create_milestone_checkout(
        self, milestone: Milestone, job_title: str, client_email: str
    ) -> dict[str, Any]:
        """Create a Stripe Checkout Session for a milestone payment."""
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Milestone: {milestone.title}",
                            "description": f"Payment for {job_title} - {milestone.title}",
                        },
                        "unit_amount": milestone.amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "milestone_id": milestone.id,
                "job_id": milestone.job_id,
                "payment_kind": "milestone",
            },
            customer_email=client_email,
            success_url=settings.stripe_success_url,
        )

        async with async_session() as db:
            result = await db.execute(
                select(Milestone).where(Milestone.id == milestone.id)
            )
            m = result.scalar_one()
            m.stripe_checkout_session_id = session.id
            await db.commit()

        return {
            "checkout_session_id": session.id,
            "checkout_url": session.url,
            "amount_cents": milestone.amount_cents,
            "milestone_id": milestone.id,
        }

    async def create_change_order_checkout(
        self, change_order: ChangeOrder, job_title: str, client_email: str
    ) -> dict[str, Any]:
        """Create a Stripe Checkout Session for a change order payment."""
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Change Order: {change_order.title}",
                            "description": change_order.description[:500],
                        },
                        "unit_amount": change_order.amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "change_order_id": change_order.id,
                "job_id": change_order.job_id,
                "payment_kind": "change_order",
            },
            customer_email=client_email,
            success_url=settings.stripe_success_url,
        )

        async with async_session() as db:
            result = await db.execute(
                select(ChangeOrder).where(ChangeOrder.id == change_order.id)
            )
            co = result.scalar_one()
            co.stripe_checkout_session_id = session.id
            co.status = ChangeOrderStatus.INVOICED
            await db.commit()

        return {
            "checkout_session_id": session.id,
            "checkout_url": session.url,
            "amount_cents": change_order.amount_cents,
            "change_order_id": change_order.id,
        }

    async def is_event_processed(self, event_id: str) -> bool:
        """Check if a Stripe webhook event has already been processed (idempotency)."""
        async with async_session() as db:
            result = await db.execute(
                select(WebhookEvent).where(WebhookEvent.stripe_event_id == event_id)
            )
            return result.scalar_one_or_none() is not None

    async def record_event(self, event_id: str, event_type: str, summary: str = ""):
        """Record a processed webhook event for idempotency."""
        async with async_session() as db:
            event = WebhookEvent(
                stripe_event_id=event_id,
                event_type=event_type,
                payload_summary=summary[:1000] if summary else "",
            )
            db.add(event)
            await db.commit()
