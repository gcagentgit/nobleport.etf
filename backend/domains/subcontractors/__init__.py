"""
NoblePort Subcontractors Domain

Subcontractor directory, bid intake, job assignment, insurance compliance,
and payment tracking.
"""

from backend.domains.subcontractors.models import (
    AssignmentStatus,
    BidStatus,
    Subcontractor,
    SubcontractorAssignment,
    SubcontractorBid,
    SubcontractorPayment,
)
from backend.domains.subcontractors.routes import router
from backend.domains.subcontractors.service import SubcontractorsService

__all__ = [
    "AssignmentStatus",
    "BidStatus",
    "Subcontractor",
    "SubcontractorAssignment",
    "SubcontractorBid",
    "SubcontractorPayment",
    "SubcontractorsService",
    "router",
]
