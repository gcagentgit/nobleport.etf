"""
System Typology API

Serves the unified 8-layer dashboard typology.
Every module, widget, and data source is classified by operational layer
and deployment status.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from backend.config.operational_truth import (
    DeploymentStatus,
    OPERATIONAL_TRUTH,
    get_status_summary,
)

router = APIRouter()

LAYERS = [
    {
        "id": "revenue",
        "name": "Revenue",
        "subtitle": "Lead → Cash Engine",
        "systems": ["Stephanie.ai Intake", "GCagent.ai", "Stripe", "HubSpot", "QuickBooks"],
    },
    {
        "id": "operations",
        "name": "Operations",
        "subtitle": "Field Execution OS",
        "systems": ["GCagent.ai", "PermitStream.ai", "Buildertrend", "Scheduling Engine"],
    },
    {
        "id": "compliance",
        "name": "Compliance",
        "subtitle": "Human-Gated Institutional Controls",
        "systems": ["Cyborg.ai", "KYC Engine", "Permit Compliance", "Risk Flags"],
    },
    {
        "id": "governance",
        "name": "Governance",
        "subtitle": "DAO & Treasury Approval",
        "systems": ["Nemoclaw", "Multi-sig Gateway", "Snapshot"],
    },
    {
        "id": "ai_orchestration",
        "name": "AI Orchestration",
        "subtitle": "Stephanie.ai Agent Mesh",
        "systems": ["Stephanie.ai", "GCagent.ai", "PermitStream.ai", "Cyborg.ai", "DeepAgent"],
    },
    {
        "id": "infrastructure",
        "name": "Infrastructure",
        "subtitle": "Sovereign Infrastructure Mesh",
        "systems": ["FastAPI", "Redis", "PostgreSQL", "LiveKit", "ElevenLabs"],
    },
    {
        "id": "audit",
        "name": "Audit & Truth",
        "subtitle": "Immutable Operational Ledger",
        "systems": ["AuditBeacon", "Merkle Anchors", "EIP-712 Registry"],
    },
    {
        "id": "client_experience",
        "name": "Client Experience",
        "subtitle": "Stephanie.ai Front Door",
        "systems": ["Voice Agent", "Avatar", "Homeowner Portal", "Intake Queue"],
    },
]

MODULES: list[dict[str, Any]] = [
    # Revenue
    {"id": "stephanie-intake", "name": "Stephanie.ai Intake", "layer": "revenue", "status": "LIVE"},
    {"id": "proposal-engine", "name": "Proposal Generation", "layer": "revenue", "status": "LIVE"},
    {"id": "deposit-collection", "name": "Deposit Collection", "layer": "revenue", "status": "STAGED"},
    {"id": "awo-tracking", "name": "AWO Tracking", "layer": "revenue", "status": "LIVE"},
    {"id": "invoice-ar", "name": "Invoice & AR", "layer": "revenue", "status": "STAGED"},
    {"id": "crm-sync", "name": "CRM Sync", "layer": "revenue", "status": "STAGED"},
    # Operations
    {"id": "gcagent-ops", "name": "GCagent.ai", "layer": "operations", "status": "LIVE"},
    {"id": "permitstream", "name": "PermitStream.ai", "layer": "operations", "status": "STAGED"},
    {"id": "scheduling", "name": "Scheduling Engine", "layer": "operations", "status": "LIVE"},
    {"id": "inspection-tracking", "name": "Inspection Tracking", "layer": "operations", "status": "MODELED"},
    {"id": "punch-list", "name": "Punch List System", "layer": "operations", "status": "MODELED"},
    # Compliance
    {"id": "permit-compliance", "name": "Permit Compliance", "layer": "compliance", "status": "STAGED"},
    {"id": "kyc-queue", "name": "KYC Queue", "layer": "compliance", "status": "MODELED"},
    {"id": "risk-flags", "name": "Risk Flags", "layer": "compliance", "status": "MODELED"},
    {"id": "command-freeze", "name": "Command Freeze", "layer": "compliance", "status": "LIVE"},
    # Governance
    {"id": "nemoclaw", "name": "Nemoclaw Policy Engine", "layer": "governance", "status": "MODELED"},
    {"id": "treasury-approval", "name": "Treasury Approval Queue", "layer": "governance", "status": "MODELED"},
    {"id": "dao-votes", "name": "DAO Voting", "layer": "governance", "status": "MODELED"},
    # AI Orchestration
    {"id": "stephanie-orchestrator", "name": "Stephanie.ai", "layer": "ai_orchestration", "status": "LIVE"},
    {"id": "gcagent-agent", "name": "GCagent.ai Agent", "layer": "ai_orchestration", "status": "LIVE"},
    {"id": "permitstream-agent", "name": "PermitStream.ai Agent", "layer": "ai_orchestration", "status": "STAGED"},
    {"id": "cyborg-agent", "name": "Cyborg.ai", "layer": "ai_orchestration", "status": "MODELED"},
    {"id": "deepagent", "name": "DeepAgent", "layer": "ai_orchestration", "status": "MODELED"},
    # Infrastructure
    {"id": "fastapi-gateway", "name": "FastAPI Gateway", "layer": "infrastructure", "status": "LIVE"},
    {"id": "voice-pipeline", "name": "Voice Pipeline", "layer": "infrastructure", "status": "LIVE"},
    {"id": "database", "name": "PostgreSQL", "layer": "infrastructure", "status": "LIVE"},
    {"id": "task-queue", "name": "Redis Task Queue", "layer": "infrastructure", "status": "STAGED"},
    # Audit — IMPORTANT: "Proposed Audit Architecture" is SPECIFICATION,
    # separated from "Production Logging" which is LIVE.
    {"id": "production-logging", "name": "Production Logging", "layer": "audit", "status": "LIVE"},
    {"id": "awo-history", "name": "AWO History", "layer": "audit", "status": "LIVE"},
    {"id": "permit-history", "name": "Permit History", "layer": "audit", "status": "STAGED"},
    {"id": "audit-beacon", "name": "AuditBeacon (Proposed)", "layer": "audit", "status": "SPECIFICATION"},
    {"id": "merkle-anchors", "name": "Merkle Anchors (Proposed)", "layer": "audit", "status": "SPECIFICATION"},
    # Client Experience — voice maturity labels visible per capability
    {"id": "voice-inbound", "name": "Voice Intake (Inbound)", "layer": "client_experience", "status": "STAGED"},
    {"id": "voice-outbound", "name": "Voice Intake (Outbound)", "layer": "client_experience", "status": "STAGED"},
    {"id": "streaming-ui", "name": "Streaming Transcript UI", "layer": "client_experience", "status": "STAGED"},
    {"id": "avatar-render", "name": "Real-Time Avatar", "layer": "client_experience", "status": "SPECIFICATION"},
    {"id": "homeowner-portal", "name": "Homeowner Portal", "layer": "client_experience", "status": "SPECIFICATION"},
    {"id": "multilingual-voice", "name": "Multilingual Voice", "layer": "client_experience", "status": "MODELED"},
    {"id": "sentiment-analytics", "name": "Customer Sentiment", "layer": "client_experience", "status": "MODELED"},
]


@router.get("/layers")
async def get_layers() -> dict[str, Any]:
    """Returns all 8 operational layers with their system assignments."""
    return {"layers": LAYERS}


@router.get("/modules")
async def get_modules(
    layer: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    """Returns all system modules, optionally filtered by layer or status."""
    items = MODULES
    if layer:
        items = [m for m in items if m["layer"] == layer]
    if status:
        items = [m for m in items if m["status"] == status.upper()]
    return {
        "total": len(items),
        "modules": items,
    }


@router.get("/summary")
async def get_typology_summary() -> dict[str, Any]:
    """Status counts across all modules."""
    counts: dict[str, int] = {
        "LIVE": 0, "STAGED": 0, "MODELED": 0, "EXTERNAL": 0,
        "SPECIFICATION": 0, "BLOCKED": 0, "ARCHIVED": 0,
    }
    for m in MODULES:
        s = m["status"]
        counts[s] = counts.get(s, 0) + 1
    return {
        "total_modules": len(MODULES),
        "total_layers": len(LAYERS),
        "status_counts": counts,
        "live_percentage": round(counts["LIVE"] / len(MODULES) * 100, 1),
        "note": (
            "Only LIVE features may be labeled 'canonical'. "
            "All other statuses must display their classification badge visibly."
        ),
    }
