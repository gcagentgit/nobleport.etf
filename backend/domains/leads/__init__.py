"""
NoblePort Leads Domain

Pipeline management for qualified leads — scoring, stage advancement,
reassignment, archival, and funnel analytics.
"""

from backend.domains.leads.routes import router
from backend.domains.leads.service import LeadsService

__all__ = ["LeadsService", "router"]
