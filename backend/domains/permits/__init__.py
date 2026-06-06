"""
NoblePort Permits Domain

Permit applications, AHJ tracking, corrections, issuance, and inspections.
"""

from backend.domains.permits.routes import router
from backend.domains.permits.service import PermitsService

__all__ = ["PermitsService", "router"]
