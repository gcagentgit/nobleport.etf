"""
Treasury / chain terminal feed.

Serves only data the backend genuinely owns LOCALLY (no outbound network):
  * snapshot  — the tamper-evident SHA-256 audit chain head + integrity check
  * services  — real configuration/health of each integration
  * chain     — the Arbitrum RPC config + token definitions the BROWSER uses to
                fetch live block/gas/balances directly (public RPC, no key)
  * feeds     — honest availability flags for sources with no live backend
                (websocket throughput, trade tape) — never fabricated

Live chain numbers are fetched client-side precisely because this backend may
sit behind a network allowlist that blocks public RPC hosts; the end-user's
browser is not subject to that policy.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter

from backend.config.operational_truth import get_feature_status
from backend.config.settings import settings
from backend.services.audit_log import AuditLog
from backend.services.stephanie_avatar import is_configured as avatar_configured

router = APIRouter()

_audit = AuditLog(settings.audit_log_path)


def _service(name: str, configured: bool, detail: str) -> dict[str, str]:
    return {
        "name": name,
        "status": "UP" if configured else "UNCONFIGURED",
        "detail": detail,
    }


@router.get("/overview")
async def overview() -> dict[str, Any]:
    intact, detail = _audit.verify_chain()
    head = _audit.head()

    snapshot: dict[str, Any] = {
        "available": head is not None,
        "intact": intact,
        "detail": detail,
        "seq": head["seq"] if head else 0,
        "hash": head["hash"] if head else None,
        "ts": head["ts"] if head else None,
        "status": ("ANCHORED" if intact else "DOWN") if head else "PENDING",
    }

    tokens: list[dict[str, Any]] = [
        {"symbol": "USDC", "address": settings.arbitrum_usdc_address, "decimals": 6},
    ]
    if settings.nbpt_token_address:
        tokens.append(
            {
                "symbol": "NBPT",
                "address": settings.nbpt_token_address,
                "decimals": settings.nbpt_token_decimals,
            }
        )

    chain = {
        "rpcUrl": settings.arbitrum_rpc_url,
        "chainId": settings.arbitrum_chain_id,
        "wallet": settings.treasury_wallet_address,
        "tokens": tokens,
    }

    services = [
        _service(
            "Audit chain (SHA-256)",
            intact and head is not None,
            f"seq {snapshot['seq']} · {detail}",
        ),
        _service(
            "Treasury wallet",
            settings.treasury_wallet_address is not None,
            settings.treasury_wallet_address or "no address configured",
        ),
        _service(
            "NBPT token", settings.nbpt_token_address is not None,
            settings.nbpt_token_address or "no contract configured",
        ),
        _service(
            "Stephanie avatar", avatar_configured(),
            f"model {settings.avatar_model}" if avatar_configured() else "no OpenAI key",
        ),
        _service("Stripe", settings.stripe_secret_key is not None, "payments"),
        _service(
            "HubSpot", settings.hubspot_sync_enabled, "CRM sync"
        ),
        _service(
            "Buildertrend",
            settings.buildertrend_api_key is not None
            or settings.buildertrend_username is not None,
            f"mode {settings.buildertrend_sync_mode.value}",
        ),
    ]

    feature_status = get_feature_status("treasury_terminal")
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "deploymentStatus": feature_status.value if feature_status else "UNREGISTERED",
        "snapshot": snapshot,
        "chain": chain,
        "services": services,
        # No real backend source for these — flagged, never invented.
        "feeds": {
            "websocket": {"available": False, "note": "no live telemetry source wired"},
            "trades": {"available": False, "note": "no execution feed wired"},
        },
    }
