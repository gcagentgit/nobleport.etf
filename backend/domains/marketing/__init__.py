"""
NoblePort Marketing Domain

Campaigns, marketing assets, spend tracking, and lead attribution.
"""

from backend.domains.marketing.models import Campaign, LeadAttribution, MarketingAsset
from backend.domains.marketing.routes import router
from backend.domains.marketing.service import MarketingService

__all__ = [
    "Campaign",
    "LeadAttribution",
    "MarketingAsset",
    "MarketingService",
    "router",
]
