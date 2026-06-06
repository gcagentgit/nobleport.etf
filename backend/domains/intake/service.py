"""
NoblePort Intake Service

Business logic for first-touch lead capture and qualification.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.lead import Lead, LeadSource, LeadStatus


# Source string -> LeadSource enum
_SOURCE_MAP: dict[str, LeadSource] = {
    "web": LeadSource.WEBSITE,
    "website": LeadSource.WEBSITE,
    "phone": LeadSource.COLD_CALL,
    "email": LeadSource.OTHER,
    "referral": LeadSource.REFERRAL,
    "social": LeadSource.SOCIAL_MEDIA,
    "partner": LeadSource.PARTNER,
    "trade_show": LeadSource.TRADE_SHOW,
}


class IntakeService:
    """First-touch capture, qualification, and routing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def capture(self, source: str, payload: dict[str, Any]) -> Lead:
        """Create a Lead from an inbound form / webhook / phone-log payload."""
        lead_source = _SOURCE_MAP.get(source.lower(), LeadSource.OTHER)

        lead = Lead(
            first_name=payload.get("first_name") or "Unknown",
            last_name=payload.get("last_name") or "Unknown",
            email=payload.get("email"),
            phone=payload.get("phone"),
            company=payload.get("company"),
            source=lead_source,
            status=LeadStatus.NEW,
            estimated_value=payload.get("estimated_value"),
            notes=payload.get("notes") or payload.get("message"),
            property_address=payload.get("property_address"),
            city=payload.get("city"),
            state=payload.get("state"),
            zip_code=payload.get("zip_code"),
        )
        self.db.add(lead)
        await self.db.commit()
        await self.db.refresh(lead)
        return lead

    async def qualify(self, lead_id: str, signals: dict[str, Any]) -> dict[str, Any]:
        """Compute a qualification score and route the lead.

        Signals may include: budget, timeline_weeks, scope, in_service_area (bool).
        Returns {lead, score, route} where route is 'fast_track' | 'nurture' | 'disqualified'.
        """
        lead = await self.db.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        score = 0
        budget = signals.get("budget") or 0
        if budget >= 250_000:
            score += 40
        elif budget >= 75_000:
            score += 25
        elif budget >= 25_000:
            score += 10

        timeline = signals.get("timeline_weeks")
        if timeline is not None and timeline <= 8:
            score += 20
        elif timeline is not None and timeline <= 26:
            score += 10

        if signals.get("in_service_area", True):
            score += 20
        else:
            score -= 30

        if signals.get("scope"):
            score += 10

        if score >= 60:
            route = "fast_track"
            lead.status = LeadStatus.QUALIFIED
        elif score >= 25:
            route = "nurture"
            lead.status = LeadStatus.CONTACTED
        else:
            route = "disqualified"
            lead.status = LeadStatus.ARCHIVED

        if budget:
            lead.estimated_value = float(budget)

        await self.db.commit()
        await self.db.refresh(lead)
        return {"lead": lead, "score": score, "route": route}

    async def assign(self, lead_id: str, owner: str) -> Lead:
        """Assign a lead to a sales rep."""
        lead = await self.db.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        lead.assigned_to = owner
        if lead.status == LeadStatus.NEW:
            lead.status = LeadStatus.CONTACTED
        await self.db.commit()
        await self.db.refresh(lead)
        return lead

    async def sources_last_30_days(self) -> list[dict[str, Any]]:
        """Count leads by source over the last 30 days."""
        since = datetime.now(timezone.utc) - timedelta(days=30)
        stmt = (
            select(Lead.source, func.count(Lead.id).label("count"))
            .where(Lead.created_at >= since)
            .group_by(Lead.source)
        )
        rows = (await self.db.execute(stmt)).all()
        return [
            {"source": row.source.value, "count": row.count}
            for row in rows
        ]
