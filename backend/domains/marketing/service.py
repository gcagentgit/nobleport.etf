"""
NoblePort Marketing Service

Campaigns, spend, attribution, and ROI logic.
"""

import json
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.marketing.models import (
    Campaign,
    CampaignChannel,
    CampaignStatus,
    LeadAttribution,
    TouchType,
)
from backend.models.estimate import Estimate, EstimateStatus
from backend.models.lead import Lead


class MarketingService:
    """Campaigns + attribution operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Campaigns
    # ------------------------------------------------------------------
    async def create_campaign(
        self,
        name: str,
        channel: str,
        budget: float = 0.0,
        start_date: date | None = None,
        end_date: date | None = None,
        target_audience: str | None = None,
        goals: dict[str, Any] | None = None,
        utm_source: str | None = None,
        utm_medium: str | None = None,
        utm_campaign: str | None = None,
    ) -> Campaign:
        campaign = Campaign(
            name=name,
            channel=CampaignChannel(channel),
            status=CampaignStatus.DRAFT,
            budget=budget,
            start_date=start_date,
            end_date=end_date,
            target_audience=target_audience,
            goals=json.dumps(goals) if goals else None,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
        )
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def list_campaigns(self) -> list[Campaign]:
        result = await self.db.execute(
            select(Campaign).order_by(Campaign.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_campaign(self, campaign_id: str) -> Campaign:
        campaign = await self.db.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        return campaign

    async def update_campaign(self, campaign_id: str, updates: dict[str, Any]) -> Campaign:
        campaign = await self.get_campaign(campaign_id)
        for key, value in updates.items():
            if key == "channel" and value is not None:
                value = CampaignChannel(value)
            if key == "status" and value is not None:
                value = CampaignStatus(value)
            if key == "goals" and isinstance(value, dict):
                value = json.dumps(value)
            if hasattr(campaign, key):
                setattr(campaign, key, value)
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def pause_campaign(self, campaign_id: str) -> Campaign:
        campaign = await self.get_campaign(campaign_id)
        campaign.status = CampaignStatus.PAUSED
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def record_spend(self, campaign_id: str, amount: float) -> Campaign:
        if amount < 0:
            raise ValueError("Spend amount must be non-negative")
        campaign = await self.get_campaign(campaign_id)
        campaign.spent = (campaign.spent or 0.0) + amount
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    # ------------------------------------------------------------------
    # Attribution
    # ------------------------------------------------------------------
    async def attribute_lead(
        self, lead_id: str, utm_params: dict[str, str]
    ) -> LeadAttribution | None:
        """Match a lead to a campaign via UTM and record the touch."""
        lead = await self.db.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        # Try to match by utm_campaign first, then source/medium combo.
        clauses = []
        if utm_params.get("utm_campaign"):
            clauses.append(Campaign.utm_campaign == utm_params["utm_campaign"])
        if utm_params.get("utm_source") and utm_params.get("utm_medium"):
            clauses.append(
                (Campaign.utm_source == utm_params["utm_source"])
                & (Campaign.utm_medium == utm_params["utm_medium"])
            )
        if not clauses:
            return None

        from sqlalchemy import or_
        campaign = (
            await self.db.execute(select(Campaign).where(or_(*clauses)).limit(1))
        ).scalars().first()
        if not campaign:
            return None

        # First touch if none recorded yet for this lead, otherwise last.
        existing = (
            await self.db.execute(
                select(func.count()).select_from(LeadAttribution).where(
                    LeadAttribution.lead_id == lead_id
                )
            )
        ).scalar() or 0
        touch_type = TouchType.FIRST if existing == 0 else TouchType.LAST

        attribution = LeadAttribution(
            lead_id=lead_id,
            campaign_id=campaign.id,
            touch_type=touch_type,
            touched_at=datetime.now(timezone.utc),
            utm_data=json.dumps(utm_params),
        )
        self.db.add(attribution)
        await self.db.commit()
        await self.db.refresh(attribution)
        return attribution

    async def get_campaign_roi(self, campaign_id: str) -> dict[str, Any]:
        """Revenue from won estimates of leads attributed to this campaign / spend."""
        campaign = await self.get_campaign(campaign_id)

        attributed_leads_stmt = select(LeadAttribution.lead_id).where(
            LeadAttribution.campaign_id == campaign_id
        )
        lead_ids = [
            row[0] for row in (await self.db.execute(attributed_leads_stmt)).all()
        ]

        revenue = 0.0
        won_count = 0
        if lead_ids:
            revenue_stmt = (
                select(func.coalesce(func.sum(Estimate.total_value), 0.0))
                .where(
                    Estimate.lead_id.in_(lead_ids),
                    Estimate.status == EstimateStatus.WON,
                )
            )
            revenue = float((await self.db.execute(revenue_stmt)).scalar() or 0.0)

            won_stmt = (
                select(func.count())
                .select_from(Estimate)
                .where(
                    Estimate.lead_id.in_(lead_ids),
                    Estimate.status == EstimateStatus.WON,
                )
            )
            won_count = int((await self.db.execute(won_stmt)).scalar() or 0)

        spent = campaign.spent or 0.0
        roi = ((revenue - spent) / spent) if spent > 0 else None

        return {
            "campaign_id": campaign.id,
            "name": campaign.name,
            "channel": campaign.channel.value,
            "spent": spent,
            "revenue": revenue,
            "leads_attributed": len(lead_ids),
            "deals_won": won_count,
            "roi": roi,
        }

    async def get_channel_performance(
        self, start: date | None = None, end: date | None = None
    ) -> list[dict[str, Any]]:
        """Aggregate spend + attributed lead count per channel within the window."""
        stmt = select(
            Campaign.channel,
            func.coalesce(func.sum(Campaign.spent), 0.0).label("spent"),
            func.coalesce(func.sum(Campaign.budget), 0.0).label("budget"),
            func.count(Campaign.id).label("campaign_count"),
        )
        if start:
            stmt = stmt.where(
                (Campaign.start_date.is_(None)) | (Campaign.start_date >= start)
            )
        if end:
            stmt = stmt.where(
                (Campaign.end_date.is_(None)) | (Campaign.end_date <= end)
            )
        stmt = stmt.group_by(Campaign.channel)
        rows = (await self.db.execute(stmt)).all()

        # Attributed leads per channel
        attr_stmt = (
            select(Campaign.channel, func.count(LeadAttribution.id))
            .join(LeadAttribution, LeadAttribution.campaign_id == Campaign.id)
            .group_by(Campaign.channel)
        )
        attr_rows = dict((await self.db.execute(attr_stmt)).all())

        return [
            {
                "channel": row.channel.value,
                "campaign_count": row.campaign_count,
                "budget": float(row.budget),
                "spent": float(row.spent),
                "leads_attributed": int(attr_rows.get(row.channel, 0) or 0),
            }
            for row in rows
        ]

    async def get_attribution_summary(self) -> dict[str, Any]:
        """Counts of leads by touch_type across all campaigns."""
        stmt = (
            select(LeadAttribution.touch_type, func.count(LeadAttribution.id))
            .group_by(LeadAttribution.touch_type)
        )
        rows = (await self.db.execute(stmt)).all()
        breakdown = {touch.value: 0 for touch in TouchType}
        for touch_type, count in rows:
            breakdown[touch_type.value] = int(count)

        total_leads_attributed = (
            await self.db.execute(
                select(func.count(func.distinct(LeadAttribution.lead_id)))
            )
        ).scalar() or 0

        return {
            "total_leads_attributed": int(total_leads_attributed),
            "touches_by_type": breakdown,
        }
