"""
NoblePort PayPal Service

PayPal Checkout integration — the secondary, consumer-convenience processor
that sits alongside Stripe. PayPal Checkout natively offers PayPal balance,
Venmo, and card funding sources, so a single order can be funded by any of
them; the funding source is recorded on the payment as ``payment_method``.

This service is fully independent of Stripe. Money is never moved between the
two processors. PayPal orders are built here, captured by PayPal, and the
resulting settlement is applied through the shared NoblePort Payment Node so
the deposit-before-start gate behaves identically to Stripe.

Order lifecycle:
  1. create_*_order  -> build a PayPal Orders v2 CREATE payload (intent CAPTURE)
  2. customer approves & the order is captured by PayPal
  3. webhook PAYMENT.CAPTURE.COMPLETED -> settle through the Payment Node
"""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import async_session
from backend.config.settings import settings
from backend.models.change_order import ChangeOrder, ChangeOrderStatus
from backend.models.estimate import Estimate
from backend.models.job import Job
from backend.models.payment import Payment, PaymentProcessor, PaymentStatus, PaymentType
from backend.services.payment_node import PaymentNode

logger = logging.getLogger(__name__)

# PayPal funding sources that should be recorded as a distinct processor.
# Venmo settles through PayPal but is tracked separately for reconciliation.
_VENMO_FUNDING = "venmo"


class PayPalService:
    """PayPal Checkout integration for the NoblePort revenue engine."""

    def __init__(self):
        self.client_id = settings.paypal_client_id
        self.client_secret = settings.paypal_client_secret
        self.webhook_id = settings.paypal_webhook_id
        self.environment = settings.paypal_environment
        self.success_url = settings.paypal_success_url
        self.cancel_url = settings.paypal_cancel_url
        self.node = PaymentNode()

    @property
    def api_base_url(self) -> str:
        """REST API base for the configured environment."""
        if self.environment == "live":
            return "https://api-m.paypal.com"
        return "https://api-m.sandbox.paypal.com"

    # =========================================================================
    # ORDER CREATION
    # =========================================================================

    async def create_deposit_order(
        self, job_id: str, db: AsyncSession
    ) -> dict[str, Any]:
        """Build a PayPal order payload for a job deposit."""
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return {"error": "Job not found"}

        if job.deposit_gate_passed:
            return {"error": "Deposit already paid", "job_id": job_id}

        est_result = await db.execute(
            select(Estimate).where(Estimate.id == job.estimate_id)
        )
        estimate = est_result.scalar_one_or_none()
        client_email = estimate.client_email if estimate else None
        client_name = estimate.client_name if estimate else "Customer"

        order_payload = self._build_order_payload(
            amount=job.deposit_required,
            name=f"Deposit - Job {job.job_number}",
            description=f"Project deposit for {client_name}",
            job_id=job_id,
            payment_type="deposit",
        )

        payment = Payment(
            job_id=job_id,
            payment_type=PaymentType.DEPOSIT,
            status=PaymentStatus.PENDING,
            amount=job.deposit_required,
            processor=PaymentProcessor.PAYPAL,
            client_name=client_name,
            client_email=client_email,
            description=f"Deposit for Job {job.job_number}",
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        return {
            "order_payload": order_payload,
            "api_base_url": self.api_base_url,
            "payment_id": payment.id,
            "amount": job.deposit_required,
            "job_id": job_id,
            "status": "order_ready",
        }

    async def create_progress_order(
        self, job_id: str, amount: float, description: str, db: AsyncSession
    ) -> dict[str, Any]:
        """Build a PayPal order payload for a progress payment."""
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return {"error": "Job not found"}

        if not job.deposit_gate_passed:
            return {"error": "Deposit must be paid before progress payments"}

        order_payload = self._build_order_payload(
            amount=amount,
            name=f"Progress Payment - Job {job.job_number}",
            description=description,
            job_id=job_id,
            payment_type="progress",
        )

        payment = Payment(
            job_id=job_id,
            payment_type=PaymentType.PROGRESS,
            status=PaymentStatus.PENDING,
            amount=amount,
            processor=PaymentProcessor.PAYPAL,
            description=description,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        return {
            "order_payload": order_payload,
            "api_base_url": self.api_base_url,
            "payment_id": payment.id,
            "amount": amount,
            "job_id": job_id,
            "status": "order_ready",
        }

    async def create_change_order_order(
        self, change_order_id: str, db: AsyncSession
    ) -> dict[str, Any]:
        """Build a PayPal order payload for a change order (AWO) payment."""
        result = await db.execute(
            select(ChangeOrder).where(ChangeOrder.id == change_order_id)
        )
        co = result.scalar_one_or_none()
        if not co:
            return {"error": "Change order not found"}

        if co.status not in (
            ChangeOrderStatus.APPROVED,
            ChangeOrderStatus.IN_PROGRESS,
        ):
            return {"error": "Change order must be approved before payment"}

        amount = (
            co.deposit_amount
            if co.requires_deposit and co.deposit_amount > 0
            else co.total_amount
        )

        order_payload = self._build_order_payload(
            amount=amount,
            name=f"Change Order {co.change_order_number}",
            description=co.title,
            job_id=co.job_id,
            payment_type="change_order",
            change_order_id=change_order_id,
        )

        payment = Payment(
            job_id=co.job_id,
            change_order_id=change_order_id,
            payment_type=PaymentType.CHANGE_ORDER,
            status=PaymentStatus.PENDING,
            amount=amount,
            processor=PaymentProcessor.PAYPAL,
            description=f"Change Order: {co.title}",
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        return {
            "order_payload": order_payload,
            "api_base_url": self.api_base_url,
            "payment_id": payment.id,
            "amount": amount,
            "change_order_id": change_order_id,
            "status": "order_ready",
        }

    def _build_order_payload(
        self,
        amount: float,
        name: str,
        description: str,
        job_id: str,
        payment_type: str,
        change_order_id: str | None = None,
    ) -> dict[str, Any]:
        """Construct a PayPal Orders v2 CREATE request body."""
        custom_id = change_order_id or job_id
        return {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "custom_id": custom_id,
                    "description": description[:127],
                    "amount": {
                        "currency_code": "USD",
                        "value": f"{amount:.2f}",
                    },
                    "items": [
                        {
                            "name": name[:127],
                            "quantity": "1",
                            "unit_amount": {
                                "currency_code": "USD",
                                "value": f"{amount:.2f}",
                            },
                        }
                    ],
                }
            ],
            "payment_source": {
                # Enables PayPal balance, Venmo, and card on the same order.
                "paypal": {
                    "experience_context": {
                        "return_url": f"{self.success_url}?job_id={job_id}",
                        "cancel_url": f"{self.cancel_url}?job_id={job_id}",
                    }
                }
            },
            "metadata": {
                "job_id": job_id,
                "change_order_id": change_order_id,
                "payment_type": payment_type,
                "nobleport_source": "revenue_engine",
            },
        }

    # =========================================================================
    # WEBHOOK PROCESSING
    # =========================================================================

    def verify_webhook_signature(self, headers: dict[str, str]) -> bool:
        """
        Validate a PayPal webhook.

        Full verification posts the transmission headers + body to PayPal's
        ``/v1/notifications/verify-webhook-signature`` endpoint. Offline we
        confirm the required transmission headers are present and a webhook id
        is configured; production deployments should complete the API
        round-trip before trusting the event.
        """
        if not self.webhook_id:
            logger.warning("PayPal webhook id not configured")
            return False

        required = (
            "paypal-transmission-id",
            "paypal-transmission-time",
            "paypal-transmission-sig",
            "paypal-cert-url",
            "paypal-auth-algo",
        )
        lowered = {k.lower(): v for k, v in headers.items()}
        return all(lowered.get(h) for h in required)

    async def handle_webhook_event(
        self, event_type: str, resource: dict[str, Any]
    ) -> dict[str, Any]:
        """Dispatch a PayPal webhook event to the right handler."""
        handlers = {
            "PAYMENT.CAPTURE.COMPLETED": self._handle_capture_completed,
            "PAYMENT.CAPTURE.DENIED": self._handle_capture_denied,
            "PAYMENT.CAPTURE.REFUNDED": self._handle_capture_refunded,
            "CUSTOMER.DISPUTE.CREATED": self._handle_dispute,
        }
        handler = handlers.get(event_type)
        if not handler:
            logger.info("Unhandled PayPal event: %s", event_type)
            return {"status": "ignored", "event_type": event_type}
        return await handler(resource)

    async def _handle_capture_completed(
        self, resource: dict[str, Any]
    ) -> dict[str, Any]:
        """PAYMENT.CAPTURE.COMPLETED -> settle through the Payment Node."""
        capture_id = resource.get("id")
        custom_id = resource.get("custom_id")
        order_id = self._extract_order_id(resource)
        amount = float(resource.get("amount", {}).get("value", 0) or 0)
        funding = self._extract_funding_source(resource)

        if not custom_id:
            return {"status": "error", "message": "No custom_id on capture"}

        async with async_session() as db:
            # custom_id is a change_order_id or a job_id.
            query = select(Payment).where(
                Payment.processor.in_(
                    [PaymentProcessor.PAYPAL, PaymentProcessor.VENMO]
                ),
                Payment.status == PaymentStatus.PENDING,
            )
            query = query.where(
                (Payment.change_order_id == custom_id)
                | (Payment.job_id == custom_id)
            )
            result = await db.execute(query.order_by(Payment.created_at.desc()))
            payment = result.scalar_one_or_none()

            if not payment:
                logger.warning(
                    "PayPal capture %s had no pending payment for %s",
                    capture_id,
                    custom_id,
                )
                return {"status": "error", "message": "No pending payment found"}

            payment.paypal_order_id = order_id
            payment.paypal_capture_id = capture_id
            payment.payment_method = funding
            if funding == _VENMO_FUNDING:
                payment.processor = PaymentProcessor.VENMO

            settled_amount = amount if amount > 0 else payment.amount
            return await self.node.apply_settlement(db, payment, settled_amount)

    async def _handle_capture_denied(
        self, resource: dict[str, Any]
    ) -> dict[str, Any]:
        """Capture denied -> mark the pending payment failed."""
        custom_id = resource.get("custom_id")
        async with async_session() as db:
            payment = await self._find_pending(db, custom_id)
            if payment:
                payment.status = PaymentStatus.FAILED
                payment.failed_at = datetime.now(timezone.utc)
                await db.commit()
        return {"status": "failed", "custom_id": custom_id}

    async def _handle_capture_refunded(
        self, resource: dict[str, Any]
    ) -> dict[str, Any]:
        """Refund -> reverse the cash from the job ledger."""
        capture_id = resource.get("id")
        refund_amount = float(resource.get("amount", {}).get("value", 0) or 0)

        async with async_session() as db:
            result = await db.execute(
                select(Payment).where(Payment.paypal_capture_id == capture_id)
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.status = PaymentStatus.REFUNDED
                job_result = await db.execute(
                    select(Job).where(Job.id == payment.job_id)
                )
                job = job_result.scalar_one_or_none()
                if job:
                    job.total_paid -= refund_amount
                await db.commit()
        return {"status": "refunded", "amount": refund_amount}

    async def _handle_dispute(self, resource: dict[str, Any]) -> dict[str, Any]:
        """Dispute opened -> flag the related payment."""
        custom_id = resource.get("custom_id")
        async with async_session() as db:
            payment = await self._find_pending(db, custom_id) or await self._find_any(
                db, custom_id
            )
            if payment:
                payment.status = PaymentStatus.DISPUTED
                await db.commit()
        logger.warning("PayPal dispute opened for %s", custom_id)
        return {"status": "disputed", "custom_id": custom_id}

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    async def _find_pending(self, db: AsyncSession, custom_id: str | None):
        if not custom_id:
            return None
        result = await db.execute(
            select(Payment)
            .where(
                Payment.status == PaymentStatus.PENDING,
                (Payment.change_order_id == custom_id)
                | (Payment.job_id == custom_id),
            )
            .order_by(Payment.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def _find_any(self, db: AsyncSession, custom_id: str | None):
        if not custom_id:
            return None
        result = await db.execute(
            select(Payment)
            .where(
                (Payment.change_order_id == custom_id)
                | (Payment.job_id == custom_id)
            )
            .order_by(Payment.created_at.desc())
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _extract_order_id(resource: dict[str, Any]) -> str | None:
        """Pull the parent order id from a capture resource's links."""
        for link in resource.get("links", []):
            href = link.get("href", "")
            if "/checkout/orders/" in href:
                return href.rstrip("/").split("/")[-1]
        supplementary = resource.get("supplementary_data", {})
        related = supplementary.get("related_ids", {}) if supplementary else {}
        return related.get("order_id")

    @staticmethod
    def _extract_funding_source(resource: dict[str, Any]) -> str:
        """
        Determine the funding source. PayPal reports Venmo captures via the
        wallet/payment_source; default to "paypal" when not specified.
        """
        source = resource.get("payment_source") or {}
        if "venmo" in source:
            return _VENMO_FUNDING
        if "card" in source:
            return "card"
        return "paypal"
