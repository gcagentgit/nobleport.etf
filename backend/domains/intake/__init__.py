"""
NoblePort Intake Domain

First-touch lead capture, qualification, and routing to sales.
"""

from backend.domains.intake.routes import router
from backend.domains.intake.service import IntakeService

__all__ = ["IntakeService", "router"]
