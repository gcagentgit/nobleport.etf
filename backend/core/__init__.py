"""
NoblePort OS Core — The operating system layer for construction revenue operations.

Modules:
    revenue_loop   — Full lifecycle orchestrator: Lead -> Maintenance
    proof_of_trust — Hash-chain audit engine for every workflow transition
    integrations   — Connector registry for HubSpot, Stripe, Calendar, etc.
"""

from backend.core.integrations import IntegrationRegistry, IntegrationStatus
from backend.core.proof_of_trust import ProofOfTrust
from backend.core.revenue_loop import RevenueLoop, RevenueLoopStage

__all__ = [
    "RevenueLoop",
    "RevenueLoopStage",
    "ProofOfTrust",
    "IntegrationRegistry",
    "IntegrationStatus",
]
