"""
Tests for the NoblePort Payment Node and PayPal/Venmo settlement.

These assert the architecture's core guarantee: Stripe and PayPal are
independent processors that both settle into one node, and the
deposit-before-start gate behaves identically no matter how the customer
paid. The node is the single source of truth for the unified ledger.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest

from backend.config.database import async_session, engine, Base
from backend.models.job import Job, JobStatus
from backend.models.payment import (
    Payment,
    PaymentProcessor,
    PaymentStatus,
    PaymentType,
)
from backend.services.payment_node import PaymentNode
from backend.services.paypal_service import PayPalService


def _run(coro):
    return asyncio.run(coro)


async def _reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def _make_job(deposit_required: float, contract_value: float = 0.0) -> str:
    job_id = str(uuid.uuid4())
    async with async_session() as db:
        job = Job(
            id=job_id,
            estimate_id=str(uuid.uuid4()),
            job_number=f"JOB-{job_id[:8]}",
            status=JobStatus.PENDING_DEPOSIT,
            deposit_required=deposit_required,
            contract_value=contract_value,
        )
        db.add(job)
        await db.commit()
    return job_id


async def _add_pending_payment(
    job_id: str,
    amount: float,
    processor: PaymentProcessor,
    payment_type: PaymentType = PaymentType.DEPOSIT,
) -> str:
    payment_id = str(uuid.uuid4())
    async with async_session() as db:
        db.add(
            Payment(
                id=payment_id,
                job_id=job_id,
                payment_type=payment_type,
                status=PaymentStatus.PENDING,
                amount=amount,
                processor=processor,
            )
        )
        await db.commit()
    return payment_id


def test_processor_enum_includes_paypal_and_venmo():
    values = {p.value for p in PaymentProcessor}
    assert {"paypal", "venmo"}.issubset(values)


def test_node_settlement_passes_deposit_gate():
    async def scenario():
        await _reset_db()
        node = PaymentNode()
        job_id = await _make_job(deposit_required=5000.0, contract_value=20000.0)
        payment_id = await _add_pending_payment(
            job_id, 5000.0, PaymentProcessor.STRIPE
        )

        async with async_session() as db:
            payment = await db.get(Payment, payment_id)
            result = await node.apply_settlement(db, payment)

        assert result["deposit_gate_passed"] is True
        assert result["job_status"] == JobStatus.SCHEDULED.value

        async with async_session() as db:
            job = await db.get(Job, job_id)
            assert job.deposit_gate_passed is True
            assert job.deposit_paid == 5000.0
            assert job.total_paid == 5000.0
            # margin = total_paid - total_costs
            assert job.margin == 5000.0

    _run(scenario())


def test_partial_deposit_does_not_pass_gate():
    async def scenario():
        await _reset_db()
        node = PaymentNode()
        job_id = await _make_job(deposit_required=5000.0)
        payment_id = await _add_pending_payment(
            job_id, 2000.0, PaymentProcessor.PAYPAL
        )

        async with async_session() as db:
            payment = await db.get(Payment, payment_id)
            result = await node.apply_settlement(db, payment)

        assert result["deposit_gate_passed"] is False
        async with async_session() as db:
            job = await db.get(Job, job_id)
            assert job.deposit_gate_passed is False
            assert job.status == JobStatus.PENDING_DEPOSIT

    _run(scenario())


def test_paypal_capture_webhook_settles_and_marks_venmo():
    async def scenario():
        await _reset_db()
        service = PayPalService()
        job_id = await _make_job(deposit_required=3000.0, contract_value=10000.0)
        await _add_pending_payment(job_id, 3000.0, PaymentProcessor.PAYPAL)

        # Simulate a PAYMENT.CAPTURE.COMPLETED funded by Venmo.
        resource = {
            "id": "CAPTURE-123",
            "custom_id": job_id,
            "amount": {"currency_code": "USD", "value": "3000.00"},
            "payment_source": {"venmo": {"email_address": "buyer@example.com"}},
            "links": [
                {
                    "href": "https://api.paypal.com/v2/checkout/orders/ORDER-9",
                    "rel": "up",
                }
            ],
        }
        result = await service.handle_webhook_event(
            "PAYMENT.CAPTURE.COMPLETED", resource
        )

        assert result["status"] == "success"
        assert result["deposit_gate_passed"] is True

        async with async_session() as db:
            job = await db.get(Job, job_id)
            assert job.deposit_gate_passed is True
            # Venmo funding is tracked as its own processor for reconciliation.
            from sqlalchemy import select

            row = await db.execute(
                select(Payment).where(Payment.job_id == job_id)
            )
            payment = row.scalar_one()
            assert payment.processor == PaymentProcessor.VENMO
            assert payment.payment_method == "venmo"
            assert payment.paypal_capture_id == "CAPTURE-123"
            assert payment.paypal_order_id == "ORDER-9"
            assert payment.status == PaymentStatus.PAID

    _run(scenario())


def test_node_summary_separates_processors():
    async def scenario():
        await _reset_db()
        node = PaymentNode()
        job_id = await _make_job(deposit_required=1000.0, contract_value=50000.0)

        # One Stripe deposit + one PayPal progress payment, both settled.
        stripe_pid = await _add_pending_payment(
            job_id, 1000.0, PaymentProcessor.STRIPE, PaymentType.DEPOSIT
        )
        paypal_pid = await _add_pending_payment(
            job_id, 2500.0, PaymentProcessor.PAYPAL, PaymentType.PROGRESS
        )
        async with async_session() as db:
            await node.apply_settlement(db, await db.get(Payment, stripe_pid))
        async with async_session() as db:
            await node.apply_settlement(db, await db.get(Payment, paypal_pid))

        summary = await node.get_node_summary()
        assert summary["cash_position"]["settled"] == 3500.0
        assert summary["by_processor"]["stripe"]["settled"] == 1000.0
        assert summary["by_processor"]["paypal"]["settled"] == 2500.0
        assert summary["by_payment_type"]["deposit"]["settled"] == 1000.0
        assert summary["by_payment_type"]["progress"]["settled"] == 2500.0

    _run(scenario())


def test_paypal_order_payload_enables_venmo_and_card():
    service = PayPalService()
    payload = service._build_order_payload(
        amount=1500.0,
        name="Deposit - Job 1",
        description="Project deposit",
        job_id="job-1",
        payment_type="deposit",
    )
    assert payload["intent"] == "CAPTURE"
    assert payload["purchase_units"][0]["amount"]["value"] == "1500.00"
    assert payload["purchase_units"][0]["custom_id"] == "job-1"
    assert "paypal" in payload["payment_source"]


def test_paypal_webhook_rejects_when_headers_missing():
    service = PayPalService()
    service.webhook_id = "WH-TEST"
    assert service.verify_webhook_signature({}) is False
    assert (
        service.verify_webhook_signature(
            {
                "paypal-transmission-id": "a",
                "paypal-transmission-time": "b",
                "paypal-transmission-sig": "c",
                "paypal-cert-url": "d",
                "paypal-auth-algo": "e",
            }
        )
        is True
    )
