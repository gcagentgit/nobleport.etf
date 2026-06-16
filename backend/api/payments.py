"""
NoblePort Payments API

Payment endpoints including Stripe checkout creation and webhook handling.
The deposit-before-start rule is enforced through the Stripe service.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import PaginatedResponse, PaymentResponse
from backend.config.database import get_db
from backend.models.payment import Payment, PaymentStatus, PaymentType
from backend.services.paypal_service import PayPalService
from backend.services.stripe_service import StripeService

router = APIRouter()
stripe_service = StripeService()
paypal_service = PayPalService()


@router.get("", response_model=PaginatedResponse)
async def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    job_id: str | None = None,
    status: str | None = None,
    payment_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Payment)

    if job_id:
        query = query.where(Payment.job_id == job_id)
    if status:
        query = query.where(Payment.status == PaymentStatus(status))
    if payment_type:
        query = query.where(Payment.payment_type == PaymentType(payment_type))

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Payment.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    payments = result.scalars().all()

    return PaginatedResponse(
        items=[PaymentResponse.model_validate(p) for p in payments],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentResponse.model_validate(payment)


# =========================================================================
# STRIPE CHECKOUT ENDPOINTS
# =========================================================================


@router.post("/checkout/deposit")
async def create_deposit_checkout(
    job_id: str, db: AsyncSession = Depends(get_db)
):
    """Create Stripe checkout session for a job deposit."""
    result = await stripe_service.create_deposit_checkout(job_id, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/checkout/progress")
async def create_progress_checkout(
    job_id: str,
    amount: float,
    description: str = "Progress payment",
    db: AsyncSession = Depends(get_db),
):
    """Create Stripe checkout session for a progress payment."""
    result = await stripe_service.create_progress_checkout(
        job_id, amount, description, db
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/checkout/change-order")
async def create_change_order_checkout(
    change_order_id: str, db: AsyncSession = Depends(get_db)
):
    """Create Stripe checkout session for a change order payment."""
    result = await stripe_service.create_change_order_checkout(
        change_order_id, db
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# =========================================================================
# PAYPAL / VENMO CHECKOUT ENDPOINTS
# =========================================================================
#
# PayPal Checkout is the secondary, consumer-convenience processor. It runs
# fully independently of Stripe — both settle into the NoblePort Payment Node
# rather than routing money through one another.


@router.post("/paypal/order/deposit")
async def create_paypal_deposit_order(
    job_id: str, db: AsyncSession = Depends(get_db)
):
    """Create a PayPal order for a job deposit (PayPal/Venmo/card funded)."""
    result = await paypal_service.create_deposit_order(job_id, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/paypal/order/progress")
async def create_paypal_progress_order(
    job_id: str,
    amount: float,
    description: str = "Progress payment",
    db: AsyncSession = Depends(get_db),
):
    """Create a PayPal order for a progress payment."""
    result = await paypal_service.create_progress_order(
        job_id, amount, description, db
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/paypal/order/change-order")
async def create_paypal_change_order_order(
    change_order_id: str, db: AsyncSession = Depends(get_db)
):
    """Create a PayPal order for a change order (AWO) payment."""
    result = await paypal_service.create_change_order_order(change_order_id, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# =========================================================================
# WEBHOOKS
# =========================================================================


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe webhook endpoint. Verifies signature and processes events.
    This drives: deposit paid -> job activated -> revenue recognized.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    # Verify webhook signature in production
    if stripe_service.webhook_secret and signature:
        if not stripe_service.verify_webhook_signature(payload, signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        import json
        event = json.loads(payload)
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event.get("type", "")
    event_data = event.get("data", {})

    result = await stripe_service.handle_webhook_event(event_type, event_data)
    return result


@router.post("/webhook/paypal")
async def paypal_webhook(request: Request):
    """
    PayPal webhook endpoint. Verifies the transmission and processes events.
    Settled captures feed the same deposit gate and ledger as Stripe via the
    NoblePort Payment Node.
    """
    payload = await request.body()

    if paypal_service.webhook_id:
        if not paypal_service.verify_webhook_signature(dict(request.headers)):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        import json
        event = json.loads(payload)
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event.get("event_type", "")
    resource = event.get("resource", {})

    result = await paypal_service.handle_webhook_event(event_type, resource)
    return result
