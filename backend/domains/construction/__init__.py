"""
NoblePort Construction Domain

Field operations: daily logs, crew tracking, material deliveries,
safety incidents, and active-site status.
"""

from backend.domains.construction.routes import router
from backend.domains.construction.service import ConstructionService

__all__ = ["ConstructionService", "router"]
