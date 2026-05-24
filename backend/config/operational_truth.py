"""
Operational Truth Matrix — Centralized Classification

Every feature surface in the NoblePort stack MUST carry one of these
classifications. This is the single source of truth for dashboards,
investor decks, API docs, sales demos, internal telemetry, and legal
review.

Classifications:
  LIVE           — production-verified, serving real users/data
  STAGED         — implemented, not yet in production use
  MODELED        — architectural concept with deterministic fixtures
  EXTERNAL       — third-party dependency (not our code)
  SPECIFICATION  — design document only, no implementation
  INTERNAL_R&D   — research prototype, not customer-facing

Any document labeled "CANONICAL" must exclusively contain LIVE features.
Documents containing mixed-status features must display this classification
visibly next to every non-LIVE element.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class DeploymentStatus(str, Enum):
    LIVE = "LIVE"
    STAGED = "STAGED"
    MODELED = "MODELED"
    EXTERNAL = "EXTERNAL"
    SPECIFICATION = "SPECIFICATION"
    INTERNAL_RD = "INTERNAL_R&D"


OPERATIONAL_TRUTH: dict[str, dict[str, Any]] = {
    # ── LIVE ──────────────────────────────────────────────────────────
    "voice_intake": {
        "status": DeploymentStatus.LIVE,
        "surface": "Stephanie.ai",
        "description": "Homeowner voice intake via LiveKit + ElevenLabs",
        "dependencies": ["livekit", "elevenlabs", "fastapi"],
    },
    "crew_task_routing": {
        "status": DeploymentStatus.LIVE,
        "surface": "GCagent.ai",
        "description": "Crew and subcontractor task routing from intake",
        "dependencies": ["langgraph", "redis"],
    },
    "lead_pipeline": {
        "status": DeploymentStatus.LIVE,
        "surface": "Backend",
        "description": "Lead capture, CRM sync, and pipeline management",
        "dependencies": ["hubspot", "fastapi", "postgres"],
    },
    "estimate_generation": {
        "status": DeploymentStatus.LIVE,
        "surface": "Backend",
        "description": "Estimate creation, sending, and tracking",
        "dependencies": ["fastapi", "postgres"],
    },
    "dashboard_kpis": {
        "status": DeploymentStatus.LIVE,
        "surface": "Frontend",
        "description": "Mission Control KPI tiles and pipeline funnel",
        "dependencies": ["nextjs", "tailwind"],
    },
    "production_logging": {
        "status": DeploymentStatus.LIVE,
        "surface": "Backend",
        "description": "Structured application logging (stdout/file)",
        "dependencies": ["python-logging"],
    },

    # ── STAGED ────────────────────────────────────────────────────────
    "permit_scraping": {
        "status": DeploymentStatus.STAGED,
        "surface": "PermitStream.ai",
        "description": "Municipality permit status scraping (MA towns)",
        "dependencies": ["playwright", "postgres"],
        "geo_constraint": "Massachusetts",
    },
    "treasury_workflows": {
        "status": DeploymentStatus.STAGED,
        "surface": "Backend",
        "description": "Stripe invoicing, deposit logging, payment tracking",
        "dependencies": ["stripe", "quickbooks"],
    },
    "hubspot_sync": {
        "status": DeploymentStatus.STAGED,
        "surface": "Backend",
        "description": "Bidirectional HubSpot CRM synchronization",
        "dependencies": ["hubspot"],
    },
    "calendar_scheduling": {
        "status": DeploymentStatus.STAGED,
        "surface": "Stephanie.ai",
        "description": "Google Calendar integration for job scheduling",
        "dependencies": ["google_calendar"],
    },
    "revenue_operator": {
        "status": DeploymentStatus.STAGED,
        "surface": "Stephanie.ai",
        "description": "Stalled deal detection, deposit reminders, margin alerts",
        "dependencies": ["fastapi", "postgres"],
    },
    "voice_streaming_ui": {
        "status": DeploymentStatus.STAGED,
        "surface": "Frontend",
        "description": "Real-time voice console with transcript streaming",
        "dependencies": ["livekit", "nextjs"],
    },

    # ── MODELED ───────────────────────────────────────────────────────
    "permit_forecast": {
        "status": DeploymentStatus.MODELED,
        "surface": "PermitStream.ai",
        "description": "AHJ-level permit issuance time forecasting",
        "dependencies": [],
    },
    "agent_mesh": {
        "status": DeploymentStatus.MODELED,
        "surface": "Orchestrator",
        "description": "Multi-agent health monitoring and mesh coordination",
        "dependencies": [],
    },
    "compliance_engine": {
        "status": DeploymentStatus.MODELED,
        "surface": "Cyborg.ai",
        "description": "Policy enforcement, kill switches, audit chain",
        "dependencies": [],
    },
    "job_cost_forecasting": {
        "status": DeploymentStatus.MODELED,
        "surface": "GCagent.ai",
        "description": "GP floor enforcement and cost variance prediction",
        "dependencies": [],
    },
    "multilingual_voice": {
        "status": DeploymentStatus.MODELED,
        "surface": "Stephanie.ai",
        "description": "Multi-language voice intake (Spanish, Portuguese)",
        "dependencies": ["elevenlabs"],
    },

    # ── EXTERNAL ──────────────────────────────────────────────────────
    "vercel_edge": {
        "status": DeploymentStatus.EXTERNAL,
        "surface": "Infrastructure",
        "description": "Vercel edge runtime and preview deployments",
        "dependencies": ["vercel"],
    },
    "stripe_payments": {
        "status": DeploymentStatus.EXTERNAL,
        "surface": "Treasury",
        "description": "Stripe payment processing and invoicing",
        "dependencies": ["stripe"],
    },
    "livekit_voice": {
        "status": DeploymentStatus.EXTERNAL,
        "surface": "Voice",
        "description": "LiveKit WebRTC infrastructure for voice calls",
        "dependencies": ["livekit"],
    },
    "elevenlabs_tts": {
        "status": DeploymentStatus.EXTERNAL,
        "surface": "Voice",
        "description": "ElevenLabs text-to-speech voice synthesis",
        "dependencies": ["elevenlabs"],
    },
    "hubspot_crm": {
        "status": DeploymentStatus.EXTERNAL,
        "surface": "Revenue",
        "description": "HubSpot CRM platform",
        "dependencies": ["hubspot"],
    },

    # ── SPECIFICATION ─────────────────────────────────────────────────
    "audit_beacon": {
        "status": DeploymentStatus.SPECIFICATION,
        "surface": "Audit",
        "description": "Pre-write event logging with merkle anchoring",
        "dependencies": [],
        "note": "Proposed audit architecture — not production logging",
    },
    "real_time_avatar": {
        "status": DeploymentStatus.SPECIFICATION,
        "surface": "Client Experience",
        "description": "Real-time rendered avatar for video consultations",
        "dependencies": ["webrtc", "gpu"],
        "note": "R&D design spec — latency requirements not yet met",
    },
    "homeowner_portal": {
        "status": DeploymentStatus.SPECIFICATION,
        "surface": "Client Experience",
        "description": "Client-facing project status dashboard",
        "dependencies": ["nextjs"],
    },

    # ── INTERNAL R&D ──────────────────────────────────────────────────
    "dao_governance": {
        "status": DeploymentStatus.INTERNAL_RD,
        "surface": "Nemoclaw",
        "description": "Multi-sig approval flows and proposal lifecycle",
        "dependencies": ["ethers"],
    },
    "security_tokens": {
        "status": DeploymentStatus.INTERNAL_RD,
        "surface": "Contracts",
        "description": "Security token structural design (Solana Token-2022)",
        "dependencies": ["solidity", "solana"],
        "legal_notice": (
            "STRUCTURAL DESIGN ONLY — NOT PUBLICLY OFFERED. "
            "No active securities offering, no broker-dealer activity. "
            "Requires: counsel sign-off, issuance structure finalized, "
            "transfer agent designated, exemption confirmed."
        ),
    },
    "ssi_identity": {
        "status": DeploymentStatus.INTERNAL_RD,
        "surface": "Identity",
        "description": "DID/ENS-based self-sovereign identity resolution",
        "dependencies": ["ethers", "did-resolver"],
    },
    "billion_task_systems": {
        "status": DeploymentStatus.INTERNAL_RD,
        "surface": "Research",
        "description": "Large-scale task orchestration simulation",
        "dependencies": [],
    },
}


def get_live_features() -> list[str]:
    return [k for k, v in OPERATIONAL_TRUTH.items()
            if v["status"] == DeploymentStatus.LIVE]


def get_feature_status(feature: str) -> DeploymentStatus | None:
    entry = OPERATIONAL_TRUTH.get(feature)
    return entry["status"] if entry else None


def is_production_ready(feature: str) -> bool:
    return get_feature_status(feature) == DeploymentStatus.LIVE


def get_status_summary() -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in OPERATIONAL_TRUTH.values():
        key = entry["status"].value
        counts[key] = counts.get(key, 0) + 1
    return counts


def get_legal_notices() -> list[dict[str, str]]:
    """Features with legal/regulatory notices that must be surfaced."""
    return [
        {"feature": k, "notice": v["legal_notice"]}
        for k, v in OPERATIONAL_TRUTH.items()
        if "legal_notice" in v
    ]
