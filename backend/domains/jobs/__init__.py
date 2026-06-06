"""
NoblePort Jobs Domain

Active job execution: from deposit through kickoff, progress tracking,
change orders, profitability, and closeout.
"""

from backend.domains.jobs.routes import router
from backend.domains.jobs.service import JobsService

__all__ = ["JobsService", "router"]
