"""
NoblePort Health Check Endpoint

Surfaces operational truth, command freeze, monitoring stack,
voice maturity, and legal notices for institutional reviewers.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from backend.config.command_freeze import BLOCKED_COMMANDS
from backend.config.monitoring import MONITORING_STACK, get_stack_summary
from backend.config.operational_truth import (
    OPERATIONAL_TRUTH,
    get_legal_notices,
    get_status_summary,
)
from backend.config.settings import settings
from backend.config.voice_maturity import (
    VOICE_CAPABILITIES,
    get_all_blockers,
    get_maturity_summary,
)

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment.value,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "integrations": {
            "buildertrend": {
                "configured": settings.buildertrend_api_key is not None
                or settings.buildertrend_username is not None,
                "sync_mode": settings.buildertrend_sync_mode.value,
            },
            "nobleport_etf": {
                "ens_domain": settings.nobleport_ens_domain,
                "chain_id": settings.nobleport_chain_id,
            },
        },
        "operational_truth": get_status_summary(),
        "frozen_commands": len(BLOCKED_COMMANDS),
        "voice_maturity": get_maturity_summary(),
        "monitoring_deployed": len([t for t in MONITORING_STACK if t.status.value == "deployed"]),
    }


@router.get("/health/features")
async def feature_status():
    """Operational truth matrix: deployment status for every feature surface."""
    return {
        "summary": get_status_summary(),
        "features": {
            k: {
                "status": v["status"].value,
                "surface": v["surface"],
                "description": v["description"],
                **({"legal_notice": v["legal_notice"]} if "legal_notice" in v else {}),
                **({"note": v["note"]} if "note" in v else {}),
            }
            for k, v in OPERATIONAL_TRUTH.items()
        },
        "legal_notices": get_legal_notices(),
    }


@router.get("/health/command-freeze")
async def command_freeze():
    """Lists all blocked autonomous commands and their alternatives."""
    return {
        "total_frozen": len(BLOCKED_COMMANDS),
        "commands": [
            {
                "command": cmd.command,
                "reason": cmd.reason.value,
                "description": cmd.description,
                "alternative": cmd.alternative,
            }
            for cmd in BLOCKED_COMMANDS
        ],
    }


@router.get("/health/voice")
async def voice_maturity():
    """Voice stack maturity classification with blockers."""
    return {
        "summary": get_maturity_summary(),
        "capabilities": [
            {
                "name": cap.name,
                "status": cap.status.value,
                "p95_latency_ms": cap.p95_latency_ms,
                "blockers": list(cap.blockers),
                "dependencies": list(cap.dependencies),
            }
            for cap in VOICE_CAPABILITIES
        ],
        "total_blockers": len(get_all_blockers()),
    }


@router.get("/health/monitoring")
async def monitoring_stack():
    """Canonical monitoring toolchain — deployed and planned."""
    return {
        "stack": [
            {
                "function": t.function,
                "tool": t.tool,
                "status": t.status.value,
                "rationale": t.rationale,
                "alternative": t.alternative,
            }
            for t in MONITORING_STACK
        ],
        "summary": get_stack_summary(),
    }
