"""
NoblePort Marketing Models

Campaigns, assets, and lead attribution touchpoints.
"""

from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class CampaignChannel(str, PyEnum):
    GOOGLE_ADS = "google_ads"
    FACEBOOK_ADS = "facebook_ads"
    SEO = "seo"
    EMAIL = "email"
    DIRECT_MAIL = "direct_mail"
    REFERRAL_PROGRAM = "referral_program"
    EVENT = "event"


class CampaignStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class AssetType(str, PyEnum):
    AD_CREATIVE = "ad_creative"
    LANDING_PAGE = "landing_page"
    EMAIL_TEMPLATE = "email_template"
    FLYER = "flyer"
    VIDEO = "video"
    BLOG_POST = "blog_post"


class TouchType(str, PyEnum):
    FIRST = "first"
    LAST = "last"
    ASSIST = "assist"


class Campaign(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[CampaignChannel] = mapped_column(Enum(CampaignChannel), nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False
    )

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    budget: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    spent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    target_audience: Mapped[str | None] = mapped_column(String(500), nullable=True)
    goals: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-as-text

    utm_source: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    utm_medium: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<Campaign {self.name} ({self.channel.value}/{self.status.value})>"


class MarketingAsset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketing_assets"

    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaigns.id"), nullable=False, index=True
    )
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<MarketingAsset {self.asset_type.value} {self.name}>"


class LeadAttribution(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "lead_attributions"

    lead_id: Mapped[str] = mapped_column(
        ForeignKey("leads.id"), nullable=False, index=True
    )
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaigns.id"), nullable=False, index=True
    )
    touch_type: Mapped[TouchType] = mapped_column(Enum(TouchType), nullable=False)
    touched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    utm_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-as-text

    def __repr__(self) -> str:
        return f"<LeadAttribution lead={self.lead_id} campaign={self.campaign_id} {self.touch_type.value}>"
