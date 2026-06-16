"""
NoblePort Payment Node API

The unified payment surface — a single pane of glass over every processor
(Stripe, PayPal, Venmo, ACH, ...). Stripe and PayPal stay independent; this
node is where they converge into one ledger and cash-position view that feeds
the Project Ledger, Job Costing, and CFO console.
"""

from fastapi import APIRouter, Query

from backend.services.payment_node import PaymentNode

router = APIRouter()
node = PaymentNode()


@router.get("/summary")
async def node_summary():
    """Cross-processor cash position and per-processor breakdown."""
    return await node.get_node_summary()


@router.get("/ledger")
async def node_ledger(
    processor: str | None = Query(None, description="Filter by processor"),
    status: str | None = Query(None, description="Filter by payment status"),
    limit: int = Query(100, ge=1, le=500),
):
    """Unified, chronological ledger across all processors."""
    return await node.get_ledger(processor=processor, status=status, limit=limit)
