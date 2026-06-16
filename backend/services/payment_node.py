"""
NoblePort Payment Node

The single source of truth for money entering NoblePort. Stripe and PayPal
are independent processors — money is never routed from one into the other.
Instead, both settle into this node, which:

  1. Applies the financial effects of a settled payment to the underlying
     Job / Change Order (the deposit gate, progress tracking, margin recalc).
     This logic lives here once and is shared by every processor so the
     deposit-before-start rule is enforced identically regardless of how the
     customer paid.

  2. Exposes a unified ledger and cash-position view across all processors —
     the construction-side equivalent of a CFO console. This is what feeds
     the Project Ledger, Job Costing, and Cash Position dashboards.

Architecture (see docs/payments/payment-node-architecture.md):

    Stripe Checkout ─┐
    PayPal / Venmo ──┼──► NoblePort Payment Node ──► Unified Ledger
    ACH / Wire / ... ┘                                Job Costing
                                                      Cash Position
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import async_session
from backend.models.change_order import ChangeOrder
from backend.models.job import Job, JobStatus
from backend.models.payment import Payment, PaymentProcessor, PaymentStatus, PaymentType

logger = logging.getLogger(__name__)


class PaymentNode:
    """Unified settlement + ledger node for all NoblePort payment processors."""

    # =========================================================================
    # SETTLEMENT  (shared by every processor)
    # =========================================================================

    async def apply_settlement(
        self,
        db: AsyncSession,
        payment: Payment,
        paid_amount: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Apply a settled payment to its Job (and Change Order, if any).

        The caller is responsible for having set the processor-specific
        identifiers (Stripe intent id, PayPal capture id, etc.) on ``payment``
        and added it to the session. This method marks it PAID, runs the
        deposit gate, updates totals/margin, and commits.

        Returns a summary describing the financial effect.
        """
        amount = paid_amount if paid_amount is not None else payment.amount

        if payment.status != PaymentStatus.PAID:
            payment.status = PaymentStatus.PAID
        if payment.paid_at is None:
            payment.paid_at = datetime.now(timezone.utc)

        job_result = await db.execute(select(Job).where(Job.id == payment.job_id))
        job = job_result.scalar_one_or_none()

        deposit_gate_passed = None
        job_status = None

        if job:
            if payment.payment_type == PaymentType.DEPOSIT:
                job.deposit_paid += amount
                job.deposit_paid_at = datetime.now(timezone.utc)

                # DEPOSIT GATE: pass once the deposit meets or exceeds required.
                if job.deposit_paid >= job.deposit_required:
                    job.deposit_gate_passed = True
                    if job.status == JobStatus.PENDING_DEPOSIT:
                        job.status = JobStatus.SCHEDULED
                    logger.info(
                        "Deposit gate PASSED for job %s via %s. Paid: $%0.2f / "
                        "Required: $%0.2f",
                        job.job_number,
                        payment.processor.value,
                        job.deposit_paid,
                        job.deposit_required,
                    )

            job.total_paid += amount

            if job.contract_value > 0:
                job.margin = job.total_paid - job.total_costs
                job.margin_percent = (job.margin / job.contract_value) * 100

            deposit_gate_passed = job.deposit_gate_passed
            job_status = job.status.value

        # Change order settlement
        if payment.change_order_id:
            co_result = await db.execute(
                select(ChangeOrder).where(ChangeOrder.id == payment.change_order_id)
            )
            co = co_result.scalar_one_or_none()
            if co:
                co.amount_paid += amount
                if co.amount_paid >= co.total_amount:
                    co.fully_paid = True
                if job:
                    job.change_order_total += amount

        await db.commit()

        return {
            "status": "success",
            "payment_id": payment.id,
            "processor": payment.processor.value,
            "payment_type": payment.payment_type.value,
            "job_id": payment.job_id,
            "amount": amount,
            "deposit_gate_passed": deposit_gate_passed,
            "job_status": job_status,
        }

    # =========================================================================
    # UNIFIED LEDGER  (single source of truth across processors)
    # =========================================================================

    async def get_node_summary(self) -> dict[str, Any]:
        """
        Cross-processor cash position for the CFO console / dashboard.

        Reports settled (paid) cash, pending (in-flight) cash, and a
        per-processor breakdown — without ever co-mingling the processors.
        """
        async with async_session() as db:
            settled = await self._sum_by(db, PaymentStatus.PAID)
            pending = await self._sum_by(
                db, PaymentStatus.PENDING, PaymentStatus.PROCESSING
            )
            by_processor = await self._breakdown_by_processor(db)
            by_type = await self._breakdown_by_type(db)

        return {
            "node": "nobleport-payment-node",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "cash_position": {
                "settled": round(settled["amount"], 2),
                "pending": round(pending["amount"], 2),
                "settled_count": settled["count"],
                "pending_count": pending["count"],
            },
            "by_processor": by_processor,
            "by_payment_type": by_type,
            "processors": [p.value for p in PaymentProcessor],
        }

    async def get_ledger(
        self,
        processor: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Unified, chronological ledger of payments across all processors."""
        async with async_session() as db:
            query = select(Payment)
            if processor:
                query = query.where(
                    Payment.processor == PaymentProcessor(processor)
                )
            if status:
                query = query.where(Payment.status == PaymentStatus(status))
            query = query.order_by(Payment.created_at.desc()).limit(limit)

            result = await db.execute(query)
            payments = result.scalars().all()

        entries = [
            {
                "payment_id": p.id,
                "job_id": p.job_id,
                "change_order_id": p.change_order_id,
                "processor": p.processor.value,
                "payment_method": p.payment_method,
                "payment_type": p.payment_type.value,
                "status": p.status.value,
                "amount": p.amount,
                "currency": p.currency,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in payments
        ]

        return {
            "node": "nobleport-payment-node",
            "count": len(entries),
            "filters": {"processor": processor, "status": status},
            "entries": entries,
        }

    # ------------------------------------------------------------------ #
    # internal aggregation helpers
    # ------------------------------------------------------------------ #

    async def _sum_by(
        self, db: AsyncSession, *statuses: PaymentStatus
    ) -> dict[str, Any]:
        result = await db.execute(
            select(
                func.coalesce(func.sum(Payment.amount), 0.0),
                func.count(Payment.id),
            ).where(Payment.status.in_(statuses))
        )
        amount, count = result.one()
        return {"amount": float(amount), "count": int(count)}

    async def _breakdown_by_processor(
        self, db: AsyncSession
    ) -> dict[str, dict[str, Any]]:
        result = await db.execute(
            select(
                Payment.processor,
                func.coalesce(func.sum(Payment.amount), 0.0),
                func.count(Payment.id),
            )
            .where(Payment.status == PaymentStatus.PAID)
            .group_by(Payment.processor)
        )
        breakdown: dict[str, dict[str, Any]] = {}
        for processor, amount, count in result.all():
            key = processor.value if hasattr(processor, "value") else str(processor)
            breakdown[key] = {"settled": round(float(amount), 2), "count": int(count)}
        return breakdown

    async def _breakdown_by_type(
        self, db: AsyncSession
    ) -> dict[str, dict[str, Any]]:
        result = await db.execute(
            select(
                Payment.payment_type,
                func.coalesce(func.sum(Payment.amount), 0.0),
                func.count(Payment.id),
            )
            .where(Payment.status == PaymentStatus.PAID)
            .group_by(Payment.payment_type)
        )
        breakdown: dict[str, dict[str, Any]] = {}
        for ptype, amount, count in result.all():
            key = ptype.value if hasattr(ptype, "value") else str(ptype)
            breakdown[key] = {"settled": round(float(amount), 2), "count": int(count)}
        return breakdown
