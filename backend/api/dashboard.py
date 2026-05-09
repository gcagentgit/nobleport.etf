"""
Mission Control dashboard router.

Single source of truth for dashboard.nobleport.ai. Pulls real data from the
revenue engine, Stephanie revenue operator, and the jobs/invoices/payments
tables where it exists; falls back to Python-side fixtures for panels whose
upstream services (PermitStream live API, agent orchestrator, Cyborg.ai
audit chain, LiveKit voice gateway) are not yet wired.

Every response carries an `X-Data-Source` header:
  live    — every field came from a live service
  fixture — every field is a deterministic fixture
  mixed   — some fields live, some fixtures (e.g. /overview)

The TypeScript types live in `src/lib/dashboard/types.ts`. Keep these shapes
in sync with that file.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.models.estimate import Estimate, EstimateStatus
from backend.models.invoice import Invoice
from backend.models.job import Job, JobStatus
from backend.models.payment import Payment, PaymentStatus, PaymentType
from backend.services.revenue_engine import RevenueEngine
from backend.services.stephanie_revenue import StephanieRevenueOperator

router = APIRouter()
revenue_engine = RevenueEngine()
stephanie = StephanieRevenueOperator()


# ---------------------------------------------------------------------------
# Header / fixture helpers
# ---------------------------------------------------------------------------

LIVE = "live"
FIXTURE = "fixture"
MIXED = "mixed"


def _set_source(response: Response, source: str) -> None:
    response.headers["X-Data-Source"] = source
    # Make the indicator readable from Next.js fetch responses.
    response.headers["Access-Control-Expose-Headers"] = "X-Data-Source"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _minus(minutes: int) -> str:
    return (_now() - timedelta(minutes=minutes)).isoformat()


def _plus(minutes: int) -> str:
    return (_now() + timedelta(minutes=minutes)).isoformat()


def _money_compact(amount: float) -> str:
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:,.0f}"


# ---------------------------------------------------------------------------
# Adapters: existing models  ->  dashboard contract shapes
# ---------------------------------------------------------------------------


def _adapt_pipeline(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """RevenueEngine.get_pipeline_snapshot() -> dashboard PipelineStage[]"""
    p = snapshot.get("pipeline", {})
    j = snapshot.get("jobs", {})
    pay = snapshot.get("payments", {})
    co = snapshot.get("change_orders", {})

    return [
        {
            "id": "lead",
            "name": "Lead",
            "count": p.get("total_estimates", 0) - p.get("total_estimates_closed", 0),
            "value": float(p.get("pending_value", 0)),
            "staleCount": 0,
        },
        {
            "id": "proposal",
            "name": "Proposal",
            "count": 0,
            "value": float(p.get("pending_value", 0)),
            "staleCount": 0,
        },
        {
            "id": "deposit",
            "name": "Deposit Pending",
            "count": j.get("pending_deposit", 0),
            "value": 0.0,
            "staleCount": 0,
        },
        {
            "id": "scheduled",
            "name": "Scheduled",
            "count": 0,
            "value": 0.0,
            "staleCount": 0,
        },
        {
            "id": "production",
            "name": "In Production",
            "count": j.get("active", 0),
            "value": float(j.get("total_contract_value", 0)),
            "staleCount": 0,
        },
        {
            "id": "invoice",
            "name": "Invoicing",
            "count": co.get("total_count", 0),
            "value": float(co.get("total_value", 0)),
            "staleCount": 0,
        },
        {
            "id": "cash",
            "name": "Cash Collected",
            "count": 0,
            "value": float(pay.get("total_revenue_collected", 0)),
            "staleCount": 0,
        },
    ]


def _adapt_stalled_deals(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for d in items:
        out.append({
            "id": f"d-{d.get('estimate_id', '')}",
            "name": d.get("estimate_number", "—"),
            "client": d.get("client_name", "—"),
            "stage": "Proposal",
            "value": float(d.get("value", 0) or 0),
            "ageDays": int(d.get("days_stale", 0) or 0),
            "owner": "—",
            "nextAction": d.get("suggested_action", ""),
            "blockers": [],
            "depositRequired": False,
            "depositCollected": False,
        })
    return out


def _adapt_job(j: Job) -> dict[str, Any]:
    next_milestone = "—"
    next_at = _plus(60 * 24)
    if j.estimated_end_date:
        next_milestone = "Estimated completion"
        try:
            dt = datetime.combine(j.estimated_end_date, datetime.min.time(), tzinfo=timezone.utc)
            next_at = dt.isoformat()
        except Exception:
            pass

    blockers = []
    if not j.deposit_gate_passed and j.status == JobStatus.PENDING_DEPOSIT:
        blockers.append("Deposit not collected")

    gp_forecast = (j.margin_percent or 0) / 100.0
    gp_floor = 0.18
    if gp_forecast and gp_forecast < gp_floor:
        blockers.append(f"GP {gp_forecast * 100:.1f}% below {gp_floor * 100:.0f}% floor")

    health = "healthy"
    if blockers:
        health = "unhealthy" if any("GP" in b or "Deposit" in b for b in blockers) else "degraded"

    schedule_variance = 0
    if j.actual_end_date and j.estimated_end_date:
        schedule_variance = (j.actual_end_date - j.estimated_end_date).days

    phase_map = {
        JobStatus.PENDING_DEPOSIT: "pre-con",
        JobStatus.SCHEDULED: "mobilization",
        JobStatus.IN_PROGRESS: "production",
        JobStatus.ON_HOLD: "production",
        JobStatus.PUNCH_LIST: "punch",
        JobStatus.COMPLETE: "closeout",
        JobStatus.CANCELLED: "closeout",
    }

    return {
        "id": j.id,
        "code": j.job_number,
        "name": j.notes[:80] if j.notes else j.job_number,
        "client": "—",
        "pm": j.crew or "—",
        "phase": phase_map.get(j.status, "production"),
        "contractValue": float(j.contract_value or 0),
        "billedToDate": float(j.total_invoiced or 0),
        "costToDate": float(j.total_costs or 0),
        "gpForecast": gp_forecast,
        "gpFloor": gp_floor,
        "scheduleVariance": schedule_variance,
        "health": health,
        "blockers": blockers,
        "depositCollected": bool(j.deposit_gate_passed),
        "nextMilestone": next_milestone,
        "nextMilestoneAt": next_at,
    }


def _adapt_invoice(inv: Invoice) -> dict[str, Any]:
    days_overdue = 0
    if inv.due_date:
        delta = (_now() - inv.due_date.replace(tzinfo=timezone.utc)).days
        days_overdue = max(0, delta)
    if inv.status == "paid" or (inv.balance_due or 0) <= 0:
        days_overdue = 0

    state = "draft"
    if inv.status == "paid":
        state = "collected"
    elif inv.status == "partial" or (inv.amount_paid or 0) > 0 < (inv.balance_due or 0):
        state = "partial"
    elif days_overdue > 0:
        state = "overdue"
    elif inv.status in ("sent", "issued"):
        state = "sent"

    return {
        "id": inv.id,
        "number": inv.invoice_number,
        "job": inv.project_id or "—",
        "client": inv.vendor_name or "—",
        "amount": float(inv.total or 0),
        "daysOverdue": days_overdue,
        "status": state,
    }


# ---------------------------------------------------------------------------
# Fixture data (for panels with no live source yet)
# ---------------------------------------------------------------------------


def _kpi_fixtures() -> list[dict[str, Any]]:
    return [
        {
            "id": "voice",
            "label": "Voice Latency (p95)",
            "value": "312ms",
            "raw": 312,
            "source": "Stephanie.ai / LiveKit",
            "delta": 18,
            "deltaLabel": "15m",
            "trend": "up",
            "health": "healthy",
            "href": "/dashboard/voice",
        },
        {
            "id": "permits",
            "label": "Permit Queue",
            "value": "24",
            "raw": 24,
            "source": "PermitStream",
            "delta": -2,
            "deltaLabel": "WoW",
            "trend": "down",
            "health": "degraded",
            "hint": "4 stalled in corrections > 14d",
            "href": "/dashboard/permits",
        },
        {
            "id": "agents",
            "label": "AI Agent Health",
            "value": "108 / 112",
            "raw": 108,
            "source": "Orchestrator",
            "delta": -1,
            "deltaLabel": "1h",
            "trend": "down",
            "health": "degraded",
            "hint": "2 degraded · 2 unhealthy",
            "href": "/dashboard/agents",
        },
        {
            "id": "compliance",
            "label": "Compliance Alerts",
            "value": "3",
            "raw": 3,
            "source": "Cyborg.ai",
            "delta": 1,
            "deltaLabel": "24h",
            "trend": "up",
            "health": "degraded",
            "hint": "1 critical · 2 warnings",
            "href": "/dashboard/compliance",
        },
    ]


def _permit_fixtures() -> list[dict[str, Any]]:
    return [
        {
            "id": "p-7401",
            "number": "NWB-2026-3101",
            "job": "NP-220 Newburyport Civic",
            "ahj": "Newburyport, MA",
            "type": "Building · Commercial",
            "status": "review",
            "submittedAt": _minus(60 * 24 * 8),
            "ageDays": 8,
            "forecastIssueAt": _plus(60 * 24 * 12),
            "reviewer": "J. Hollis",
            "zoningFlags": [],
        },
        {
            "id": "p-7388",
            "number": "PLM-2026-2104",
            "job": "NP-211 Plum Island Reno",
            "ahj": "Newbury, MA (Plum Island overlay)",
            "type": "Building · Coastal AE",
            "status": "corrections",
            "submittedAt": _minus(60 * 24 * 21),
            "ageDays": 21,
            "forecastIssueAt": _plus(60 * 24 * 9),
            "reviewer": "C. Lefevre",
            "zoningFlags": ["Coastal AE-9 setback", "Wetlands NOI required"],
        },
        {
            "id": "p-7402",
            "number": "TAN-2026-0890",
            "job": "NP-198 Tannery Mills",
            "ahj": "Newburyport, MA",
            "type": "Building · Adaptive Reuse",
            "status": "review",
            "submittedAt": _minus(60 * 24 * 5),
            "ageDays": 5,
            "forecastIssueAt": _plus(60 * 24 * 16),
            "reviewer": "J. Hollis",
            "zoningFlags": ["Historic district overlay"],
        },
        {
            "id": "p-7410",
            "number": "SAL-2026-0331",
            "job": "NP-225 Salisbury Cottages",
            "ahj": "Salisbury, MA",
            "type": "Building · Residential",
            "status": "intake",
            "submittedAt": _minus(60 * 24 * 1),
            "ageDays": 1,
            "forecastIssueAt": _plus(60 * 24 * 28),
            "zoningFlags": [],
        },
        {
            "id": "p-7359",
            "number": "NWB-2026-2812",
            "job": "NP-204 Highland Phase I",
            "ahj": "Newburyport, MA",
            "type": "Electrical",
            "status": "issued",
            "submittedAt": _minus(60 * 24 * 14),
            "ageDays": 14,
            "forecastIssueAt": _minus(60 * 24 * 1),
            "reviewer": "R. Costa",
            "zoningFlags": [],
        },
    ]


def _permit_forecast() -> list[dict[str, Any]]:
    return [
        {"ahj": "Newburyport, MA", "medianDays": 11, "p90Days": 24, "open": 9, "issuedThisMonth": 6},
        {"ahj": "Newbury, MA", "medianDays": 18, "p90Days": 42, "open": 4, "issuedThisMonth": 1},
        {"ahj": "Salisbury, MA", "medianDays": 14, "p90Days": 28, "open": 5, "issuedThisMonth": 3},
        {"ahj": "Amesbury, MA", "medianDays": 9, "p90Days": 19, "open": 3, "issuedThisMonth": 4},
        {"ahj": "Boston, MA", "medianDays": 27, "p90Days": 64, "open": 3, "issuedThisMonth": 2},
    ]


def _agent_fixtures() -> list[dict[str, Any]]:
    return [
        {
            "id": "a-stephanie", "name": "Stephanie.ai", "family": "Stephanie",
            "role": "Executive voice / orchestration", "health": "healthy",
            "queueDepth": 2, "inFlight": 1, "p95LatencyMs": 312, "errorRate": 0.004,
            "uptime30d": 0.9994, "lastHeartbeat": _minus(0), "killSwitchArmed": False,
            "currentTask": "Live call · Highland follow-up",
        },
        {
            "id": "a-gcagent", "name": "GCagent.ai", "family": "GCagent",
            "role": "Construction operations supervisor", "health": "healthy",
            "queueDepth": 14, "inFlight": 3, "p95LatencyMs": 980, "errorRate": 0.011,
            "uptime30d": 0.9982, "lastHeartbeat": _minus(0), "killSwitchArmed": False,
            "currentTask": "NP-198 schedule recompute",
        },
        {
            "id": "a-permit", "name": "PermitStream.ai", "family": "PermitStream",
            "role": "Permit forecasting + AHJ workflows", "health": "degraded",
            "queueDepth": 31, "inFlight": 2, "p95LatencyMs": 2210, "errorRate": 0.034,
            "uptime30d": 0.9941, "lastHeartbeat": _minus(1), "killSwitchArmed": False,
            "currentTask": "Newbury Coastal AE redline scan",
        },
        {
            "id": "a-cyborg", "name": "Cyborg.ai", "family": "Cyborg",
            "role": "Compliance / governance enforcement", "health": "healthy",
            "queueDepth": 0, "inFlight": 0, "p95LatencyMs": 142, "errorRate": 0.0,
            "uptime30d": 1.0, "lastHeartbeat": _minus(0), "killSwitchArmed": True,
        },
        {
            "id": "a-deepagent", "name": "DeepAgent", "family": "DeepAgent",
            "role": "Long-horizon research / proposals", "health": "healthy",
            "queueDepth": 4, "inFlight": 1, "p95LatencyMs": 4810, "errorRate": 0.018,
            "uptime30d": 0.997, "lastHeartbeat": _minus(0), "killSwitchArmed": False,
            "currentTask": "Tannery Mills MEP redline",
        },
        {
            "id": "a-kuzo", "name": "KUZO", "family": "KUZO",
            "role": "Field telemetry + sensor fusion", "health": "unhealthy",
            "queueDepth": 0, "inFlight": 0, "p95LatencyMs": 0, "errorRate": 0.0,
            "uptime30d": 0.962, "lastHeartbeat": _minus(11), "killSwitchArmed": False,
        },
        {
            "id": "a-collector", "name": "AR-Collector", "family": "Other",
            "role": "AR > 30d outreach", "health": "healthy",
            "queueDepth": 6, "inFlight": 1, "p95LatencyMs": 720, "errorRate": 0.009,
            "uptime30d": 0.9991, "lastHeartbeat": _minus(0), "killSwitchArmed": False,
            "currentTask": "INV-2026-0412 follow-up",
        },
        {
            "id": "a-bidops", "name": "BidOps", "family": "Other",
            "role": "Subcontractor bid leveling", "health": "unhealthy",
            "queueDepth": 0, "inFlight": 0, "p95LatencyMs": 0, "errorRate": 1.0,
            "uptime30d": 0.94, "lastHeartbeat": _minus(34), "killSwitchArmed": False,
        },
    ]


def _agent_summary_fixture() -> dict[str, Any]:
    agents = _agent_fixtures()
    total = 112
    healthy = sum(1 for a in agents if a["health"] == "healthy") + (total - len(agents))
    degraded = sum(1 for a in agents if a["health"] == "degraded")
    unhealthy = sum(1 for a in agents if a["health"] == "unhealthy")
    return {
        "total": total,
        "healthy": healthy,
        "degraded": degraded,
        "unhealthy": unhealthy,
        "totalQueue": sum(a["queueDepth"] for a in agents),
        "totalInFlight": sum(a["inFlight"] for a in agents),
        "topLatencyMs": max((a["p95LatencyMs"] for a in agents), default=0),
    }


def _alert_fixtures() -> list[dict[str, Any]]:
    return [
        {
            "id": "c-501", "ts": _minus(48), "severity": "critical", "category": "erc1400",
            "subject": "Restricted transfer attempt",
            "detail": "ERC-1400 restriction blocked transfer of NP-RE-204 to non-whitelisted 0xb7…2c",
            "agent": "Cyborg.ai", "resolved": False,
        },
        {
            "id": "c-502", "ts": _minus(220), "severity": "warn", "category": "sanctions",
            "subject": "OFAC list refresh",
            "detail": "Daily sanctions diff applied · 14 new entries · 0 portfolio matches",
            "agent": "Cyborg.ai", "resolved": True,
        },
        {
            "id": "c-503", "ts": _minus(640), "severity": "warn", "category": "policy",
            "subject": "GP floor breach forecast",
            "detail": "Job NP-211 forecast GP 14.6% below 18% floor — escalated to PM",
            "agent": "GCagent.ai", "resolved": False,
        },
        {
            "id": "c-504", "ts": _minus(900), "severity": "info", "category": "signature",
            "subject": "HumanApprovalGateway",
            "detail": "Multi-sig 2/3 collected for NP-220 GMP amendment",
            "agent": "Cyborg.ai", "resolved": True,
        },
        {
            "id": "c-505", "ts": _minus(1300), "severity": "critical", "category": "kill-switch",
            "subject": "Kill-switch armed: tx-broadcast",
            "detail": "Operator armed kill-switch on tx-broadcast scope after RPC anomaly",
            "agent": "Operator · m.velasquez", "resolved": False,
        },
    ]


def _kill_switch_fixtures() -> list[dict[str, Any]]:
    return [
        {
            "id": "k-tx", "scope": "tx-broadcast", "armed": True,
            "lastTriggeredAt": _minus(1300),
            "controller": "m.velasquez (2/3 multi-sig)",
            "description": "Halts all on-chain broadcasts (Arbitrum + L1 anchors)",
        },
        {
            "id": "k-voice", "scope": "stephanie-outbound", "armed": False,
            "controller": "m.velasquez (1/1)",
            "description": "Disables Stephanie outbound voice initiation",
        },
        {
            "id": "k-agents", "scope": "agent-mesh-write", "armed": False,
            "controller": "m.velasquez (2/3 multi-sig)",
            "description": "Forces all agents into read-only mode",
        },
        {
            "id": "k-funds", "scope": "treasury-disbursement", "armed": False,
            "controller": "DAO 4/7",
            "description": "Halts Stripe + bank disbursement workflows",
        },
    ]


_HASHES = [
    "0x9a4f1c0b8e2c6d3f17a8b25c91d4f0e6a3b8c5d7e2f1a9b4c8d5e7f0a3b6c9d2",
    "0x7c1e9b3d5a8f2c0e4b7d1a9f6c3e8b5d2f0a7c4e9b1d6f3a0c5e8b2d7f4a1c9e",
    "0x4d8a2c6e1f5b9d3a7c0e8b4f2d6a9c5e1b3f7d0a8c2e5f9b4d7a1c6e3f0b5d8a",
    "0x1f5b8c3e9a2d7f4b0c6e1a8d3f9b5c2e7a4d0f6b8c3e1a9d5f2b7c0e4a8d6f3b",
    "0xb3e7a1d5f9c2b8d4a0e6c1f5b9d3a7c4e0f8b2d6a1c5e9b3f7d0a4c8e2b6f1d5",
    "0x6c2e9b5d1f7a3c8e4b0d6f2a9c5e1b7d3f0a8c4e9b2d6f1a5c0e7b3d8f4a2c6e",
    "0x2a8d4f0b6c1e9a5d3f7b0c4e8a2d6f1b9c5e3a7d4f0b8c2e6a1d5f9b3c7e4a0d",
]


def _audit_fixtures() -> list[dict[str, Any]]:
    return [
        {"id": "au-9911", "ts": _minus(2), "operator": "m.velasquez", "agent": "GCagent.ai",
         "action": "job.schedule.update", "subject": "NP-198 · push topping-out 4d",
         "approval": "human", "hash": _HASHES[0], "prevHash": _HASHES[1],
         "anchor": "arbitrum:0x9a…c9d2 / block 184729031", "status": "committed"},
        {"id": "au-9910", "ts": _minus(8), "operator": "system", "agent": "Cyborg.ai",
         "action": "erc1400.transfer.block",
         "subject": "NP-RE-204 · 0x4a91 → 0xb72c (non-whitelisted)",
         "approval": "auto", "hash": _HASHES[1], "prevHash": _HASHES[2],
         "status": "committed"},
        {"id": "au-9909", "ts": _minus(14), "operator": "a.park", "agent": "PermitStream.ai",
         "action": "permit.submit",
         "subject": "PLM-2026-2104 · Plum Island corrections re-submit",
         "approval": "human", "hash": _HASHES[2], "prevHash": _HASHES[3],
         "status": "committed"},
        {"id": "au-9908", "ts": _minus(22), "operator": "m.velasquez",
         "action": "kill-switch.arm", "subject": "tx-broadcast",
         "approval": "multi-sig", "hash": _HASHES[3], "prevHash": _HASHES[4],
         "anchor": "arbitrum:0x1f…5d8a / block 184728994", "status": "committed"},
        {"id": "au-9907", "ts": _minus(45), "operator": "d.iyer", "agent": "GCagent.ai",
         "action": "invoice.send",
         "subject": "INV-2026-0421 · Tannery Mills · $412,900",
         "approval": "human", "hash": _HASHES[4], "prevHash": _HASHES[5],
         "status": "committed"},
        {"id": "au-9906", "ts": _minus(78), "operator": "system", "agent": "AR-Collector",
         "action": "invoice.followup",
         "subject": "INV-2026-0412 · 22d overdue · email + voice",
         "approval": "auto", "hash": _HASHES[5], "prevHash": _HASHES[6],
         "status": "committed"},
        {"id": "au-9905", "ts": _minus(120), "operator": "m.velasquez",
         "action": "gmp.amendment.sign", "subject": "NP-220 · GMP amendment #2",
         "approval": "multi-sig", "hash": _HASHES[6], "prevHash": _HASHES[0],
         "anchor": "arbitrum:0xb3…f1d5 / block 184728812", "status": "committed"},
    ]


def _voice_session_fixture() -> dict[str, Any]:
    return {
        "active": True,
        "sessionId": "lk-sess-9b1c4e7a",
        "participants": 2,
        "latencyMs": 312,
        "packetLossPct": 0.4,
        "asrModel": "nova-3",
        "ttsVoice": "stephanie-v3",
        "startedAt": _minus(7),
        "routedTo": ["GCagent.ai", "AR-Collector"],
    }


def _voice_transcript_fixture() -> list[dict[str, Any]]:
    return [
        {"id": "t-1", "ts": _minus(7), "speaker": "stephanie",
         "text": "Hi, this is Stephanie at NoblePort following up on Highland Phase II. Do you have a moment?"},
        {"id": "t-2", "ts": _minus(6), "speaker": "caller",
         "text": "Yes — go ahead. We had architect comments back yesterday."},
        {"id": "t-3", "ts": _minus(5), "speaker": "stephanie", "routed": "GCagent.ai",
         "text": "Got it. I see proposal d-2041 is in proposal stage at $1.24M. I can route the redline to GCagent for repricing."},
        {"id": "t-4", "ts": _minus(4), "speaker": "caller",
         "text": "Please do — and confirm we still have the Q3 slot."},
        {"id": "t-5", "ts": _minus(3), "speaker": "stephanie",
         "text": "Confirming Q3 mobilization slot is held. Note: deposit must clear before scheduling per policy."},
        {"id": "t-6", "ts": _minus(1), "speaker": "operator", "routed": "AR-Collector",
         "text": "(barge-in) Stephanie, also flag this for AR-Collector — INV-0412 is open against this client."},
    ]


# ---------------------------------------------------------------------------
# Live computations (revenue + jobs)
# ---------------------------------------------------------------------------


async def _live_cash(db: AsyncSession) -> dict[str, Any]:
    deposits = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .select_from(Payment)
        .where(
            Payment.payment_type == PaymentType.DEPOSIT,
            Payment.status == PaymentStatus.PAID,
        )
    )
    revenue = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .select_from(Payment)
        .where(Payment.status == PaymentStatus.PAID)
    )
    pending_deposits = await db.execute(
        select(func.coalesce(func.sum(Job.deposit_required - Job.deposit_paid), 0))
        .select_from(Job)
        .where(Job.deposit_gate_passed == False)  # noqa: E712
    )
    pending_payables = await db.execute(
        select(func.coalesce(func.sum(Invoice.balance_due), 0))
        .select_from(Invoice)
    )

    operating = float(revenue.scalar() or 0)
    return {
        "asOf": _now().isoformat(),
        "operating": operating,
        "reserve": 0.0,
        "escrow": float(deposits.scalar() or 0),
        "pendingDeposits": float(pending_deposits.scalar() or 0),
        "pendingPayables": float(pending_payables.scalar() or 0),
        # No expense feed yet, so runway is unknown — surface 0 rather than fake.
        "runwayDays": 0,
    }


async def _live_kpis(db: AsyncSession, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    pipeline_value = (
        float(snapshot.get("pipeline", {}).get("pending_value", 0))
        + float(snapshot.get("jobs", {}).get("total_contract_value", 0))
    )
    deposits_collected = float(snapshot.get("payments", {}).get("total_deposits_collected", 0))
    active_jobs = int(snapshot.get("jobs", {}).get("active", 0))

    margin_alerts = await stephanie.detect_margin_compression()
    under_floor = len(margin_alerts)

    win_rate = float(snapshot.get("pipeline", {}).get("win_rate", 0))

    return [
        {
            "id": "pipeline", "label": "Pipeline Value",
            "value": _money_compact(pipeline_value), "raw": pipeline_value,
            "source": "Revenue Engine", "delta": None, "deltaLabel": "live",
            "trend": "flat", "health": "healthy", "href": "/dashboard/revenue",
        },
        {
            "id": "deposits", "label": "Deposits Collected",
            "value": _money_compact(deposits_collected), "raw": deposits_collected,
            "source": "Stripe / DB", "delta": None, "deltaLabel": "to date",
            "trend": "flat", "health": "healthy", "href": "/dashboard/revenue",
        },
        {
            "id": "jobs", "label": "Active Jobs",
            "value": str(active_jobs), "raw": active_jobs,
            "source": "GCagent / DB", "delta": None, "deltaLabel": "live",
            "trend": "flat", "health": "healthy", "href": "/dashboard/jobs",
        },
        {
            "id": "winrate", "label": "Win Rate",
            "value": f"{win_rate:.1f}%", "raw": win_rate / 100.0,
            "source": "Estimates", "delta": None, "deltaLabel": "to date",
            "trend": "flat",
            "health": "degraded" if win_rate < 30 else "healthy",
            "href": "/dashboard/revenue",
        },
        {
            "id": "gp", "label": "Jobs Under GP Floor",
            "value": str(under_floor), "raw": under_floor,
            "source": "Stephanie", "delta": None, "deltaLabel": "live",
            "trend": "up" if under_floor else "flat",
            "health": "unhealthy" if under_floor else "healthy",
            "hint": f"{under_floor} job(s) below 15% floor" if under_floor else None,
            "href": "/dashboard/jobs",
        },
    ]


async def _live_rules(db: AsyncSession) -> list[dict[str, Any]]:
    margin_alerts = await stephanie.detect_margin_compression(threshold_percent=18.0)
    deposit_alerts = await stephanie.get_pending_deposit_reminders()
    return [
        {"id": "r-deposit", "rule": "No deposit → no schedule",
         "status": "enforced", "violations": 0},
        {"id": "r-invoice", "rule": "No invoice → no progress",
         "status": "enforced", "violations": 0},
        {"id": "r-audit", "rule": "No audit log → no state change",
         "status": "enforced", "violations": 0},
        {"id": "r-gpfloor", "rule": "Hard GP floor (18%) on production jobs",
         "status": "warning" if margin_alerts else "enforced",
         "violations": len(margin_alerts)},
        {"id": "r-deposit-pending", "rule": "Deposit pending escalation > 7d",
         "status": "warning" if deposit_alerts else "enforced",
         "violations": sum(1 for d in deposit_alerts if d.get("severity") == "critical")},
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/health")
async def health(response: Response) -> dict[str, Any]:
    _set_source(response, LIVE)
    return {"status": "ok", "service": "dashboard.nobleport.ai", "ts": _now().isoformat()}


@router.get("/overview")
async def get_overview(
    response: Response, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    snapshot = await revenue_engine.get_pipeline_snapshot(db)
    pipeline = _adapt_pipeline(snapshot)
    cash = await _live_cash(db)
    live_kpis = await _live_kpis(db, snapshot)

    # KPIs are mixed: revenue/jobs live, voice/permits/agents/compliance fixtures
    kpis = live_kpis + _kpi_fixtures()
    alerts = [a for a in _alert_fixtures() if not a["resolved"]][:4]

    job_rows = (await db.execute(
        select(Job).where(
            Job.status.in_([JobStatus.SCHEDULED, JobStatus.IN_PROGRESS, JobStatus.PUNCH_LIST])
        ).order_by(Job.estimated_end_date.asc().nullslast()).limit(5)
    )).scalars().all()
    upcoming = [
        {
            "jobCode": j.job_number,
            "milestone": "Estimated completion" if j.estimated_end_date else "—",
            "at": (
                datetime.combine(j.estimated_end_date, datetime.min.time(), tzinfo=timezone.utc).isoformat()
                if j.estimated_end_date else _plus(60 * 24)
            ),
        }
        for j in job_rows
    ]

    _set_source(response, MIXED)
    return {
        "generatedAt": _now().isoformat(),
        "kpis": kpis,
        "alerts": alerts,
        "agentSummary": _agent_summary_fixture(),
        "cash": cash,
        "pipeline": pipeline,
        "upcomingMilestones": upcoming,
    }


@router.get("/revenue")
async def get_revenue(
    response: Response, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    snapshot = await revenue_engine.get_pipeline_snapshot(db)
    pipeline = _adapt_pipeline(snapshot)
    cash = await _live_cash(db)

    stalled = await stephanie.detect_stalled_deals()
    deals = _adapt_stalled_deals(stalled)

    inv_rows = (await db.execute(
        select(Invoice).order_by(Invoice.due_date.asc().nullslast()).limit(50)
    )).scalars().all()
    invoices = [_adapt_invoice(i) for i in inv_rows]

    rules = await _live_rules(db)

    _set_source(response, LIVE)
    return {"pipeline": pipeline, "deals": deals, "invoices": invoices, "cash": cash, "rules": rules}


@router.get("/jobs")
async def get_jobs(
    response: Response, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    rows = (await db.execute(
        select(Job).order_by(Job.created_at.desc()).limit(100)
    )).scalars().all()
    jobs = [_adapt_job(j) for j in rows]
    _set_source(response, LIVE)
    return {"jobs": jobs}


@router.get("/permits")
async def get_permits(response: Response) -> dict[str, Any]:
    _set_source(response, FIXTURE)
    return {"permits": _permit_fixtures(), "forecast": _permit_forecast()}


@router.get("/agents")
async def get_agents(response: Response) -> dict[str, Any]:
    _set_source(response, FIXTURE)
    return {"agents": _agent_fixtures(), "summary": _agent_summary_fixture()}


@router.get("/compliance")
async def get_compliance(response: Response) -> dict[str, Any]:
    _set_source(response, FIXTURE)
    return {"alerts": _alert_fixtures(), "killSwitches": _kill_switch_fixtures()}


@router.get("/audit")
async def get_audit(
    response: Response, limit: int = Query(default=50, ge=1, le=200)
) -> dict[str, Any]:
    entries = _audit_fixtures()[:limit]
    _set_source(response, FIXTURE)
    return {"entries": entries, "limit": limit}


@router.get("/voice")
async def get_voice(response: Response) -> dict[str, Any]:
    _set_source(response, FIXTURE)
    return {"session": _voice_session_fixture(), "transcript": _voice_transcript_fixture()}
