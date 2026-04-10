"""
NoblePort Health Check Endpoint
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from backend.config.settings import settings

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
    }
