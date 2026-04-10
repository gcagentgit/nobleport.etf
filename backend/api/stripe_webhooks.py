"""
NoblePort Stripe Webhook Handler

Idempotent webhook processing for all payment events.
Routes payments to the correct handler based on metadata.payment_kind:
  - deposit → job pipeline (create job + ops tasks)
  - milestone → job pipeline (mark milestone paid)
  - change_order → job pipeline (attach to job)
"""

import logging

import stripe
from fastapi import APIRouter, HTTPException, Request

from backend.config.settings import settings
from backend.services.job_pipeline import JobPipeline
from backend.services.notification_service import NotificationService
from backend.services.stripe_service import StripeService

logger = logging.getLogger(__name__)
router = APIRouter()
stripe_svc = StripeService()
pipeline = JobPipeline()
notifications = NotificationService()


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe webhook endpoint with signature verification and idempotency.
    This is where payment = commitment becomes reality.
    """
    body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    # Verify webhook signature
    if settings.stripe_webhook_secret:
        try:
            event = stripe.Webhook.construct_event(
                body, sig_header, settings.stripe_webhook_secret
            )
        except stripe.SignatureVerificationError:
            raise HTTPException(status_code=401, detail="Invalid signature")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
    else:
        import json
        event = json.loads(body)

    event_id = event.get("id", "")
    event_type = event.get("type", "")

    # Idempotency check — don't process the same event twice
    if await stripe_svc.is_event_processed(event_id):
        logger.info(f"Skipping duplicate event: {event_id}")
        return {"status": "already_processed"}

    result = {"status": "received", "event_type": event_type}

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        payment_kind = metadata.get("payment_kind", "")
        payment_intent_id = session.get("payment_intent", "")

        if payment_kind == "deposit":
            proposal_id = metadata.get("proposal_id", "")
            result = await pipeline.handle_deposit_payment(
                proposal_id=proposal_id,
                payment_intent_id=payment_intent_id,
            )
            # Notify ops team
            await notifications.notify_ops_team(
                subject=f"New Job Created - Deposit Received",
                message=f"Deposit payment confirmed. Job created from proposal {proposal_id}.",
                job_data=result,
            )

        elif payment_kind == "milestone":
            milestone_id = metadata.get("milestone_id", "")
            result = await pipeline.handle_milestone_payment(
                milestone_id=milestone_id,
                payment_intent_id=payment_intent_id,
            )

        elif payment_kind == "change_order":
            change_order_id = metadata.get("change_order_id", "")
            result = await pipeline.handle_change_order_payment(
                change_order_id=change_order_id,
                payment_intent_id=payment_intent_id,
            )

        else:
            logger.warning(f"Unknown payment_kind in webhook: {payment_kind}")

    elif event_type == "payment_intent.payment_failed":
        pi = event["data"]["object"]
        logger.warning(f"Payment failed: {pi.get('id')} - {pi.get('last_payment_error', {}).get('message', 'Unknown')}")
        result = {"status": "payment_failed", "payment_intent": pi.get("id")}

    # Record for idempotency
    await stripe_svc.record_event(
        event_id=event_id,
        event_type=event_type,
        summary=str(result),
    )

    return result
