"""
NoblePort Leads Service

Pipeline management logic for qualified leads.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.lead import Lead, LeadStatus


# Forward funnel order
_FUNNEL_ORDER: list[LeadStatus] = [
    LeadStatus.NEW,
    LeadStatus.CONTACTED,
    LeadStatus.QUALIFIED,
    LeadStatus.PROPOSAL_SENT,
    LeadStatus.NEGOTIATING,
    LeadStatus.WON,
]


class LeadsService:
    """Pipeline management for qualified leads."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get(self, lead_id: str) -> Lead:
        lead = await self.db.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        return lead

    async def score(self, lead_id: str) -> dict[str, Any]:
        """Recompute lead score from recency, value, and engagement signals."""
        lead = await self._get(lead_id)

        score = 0
        if lead.estimated_value:
            if lead.estimated_value >= 250_000:
                score += 40
            elif lead.estimated_value >= 75_000:
                score += 25
            elif lead.estimated_value >= 25_000:
                score += 10

        age_days = (datetime.now(timezone.utc) - lead.created_at).days
        if age_days <= 7:
            score += 20
        elif age_days <= 30:
            score += 10
        elif age_days > 90:
            score -= 10

        if lead.assigned_to:
            score += 10
        if lead.email and lead.phone:
            score += 10
        if lead.status in (LeadStatus.QUALIFIED, LeadStatus.PROPOSAL_SENT, LeadStatus.NEGOTIATING):
            score += 20

        return {"lead_id": lead.id, "score": max(0, min(score, 100))}

    async def advance_stage(self, lead_id: str, to_stage: str) -> Lead:
        """Move a lead forward in the funnel."""
        lead = await self._get(lead_id)
        try:
            target = LeadStatus(to_stage)
        except ValueError:
            raise ValueError(f"Invalid stage: {to_stage}")

        # Prevent silly backward jumps (still allow WON/LOST/ARCHIVED from anywhere).
        terminal = {LeadStatus.WON, LeadStatus.LOST, LeadStatus.ARCHIVED}
        if target not in terminal:
            if (
                lead.status in _FUNNEL_ORDER
                and target in _FUNNEL_ORDER
                and _FUNNEL_ORDER.index(target) < _FUNNEL_ORDER.index(lead.status)
            ):
                raise ValueError(
                    f"Cannot move backward from {lead.status.value} to {target.value}"
                )

        lead.status = target
        await self.db.commit()
        await self.db.refresh(lead)
        return lead

    async def reassign(self, lead_id: str, new_owner: str, reason: str) -> Lead:
        """Reassign a lead to a new owner; reason is appended to notes."""
        lead = await self._get(lead_id)
        old_owner = lead.assigned_to or "unassigned"
        lead.assigned_to = new_owner
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        note = f"[{stamp}] reassigned {old_owner} -> {new_owner}: {reason}"
        lead.notes = f"{lead.notes}\n{note}" if lead.notes else note
        await self.db.commit()
        await self.db.refresh(lead)
        return lead

    async def archive(self, lead_id: str, reason: str) -> Lead:
        """Archive a dead or stale lead."""
        lead = await self._get(lead_id)
        lead.status = LeadStatus.ARCHIVED
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        note = f"[{stamp}] archived: {reason}"
        lead.notes = f"{lead.notes}\n{note}" if lead.notes else note
        await self.db.commit()
        await self.db.refresh(lead)
        return lead

    async def get_funnel_snapshot(self) -> dict[str, Any]:
        """Counts per stage + stage-to-stage conversion rates."""
        stmt = select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
        rows = (await self.db.execute(stmt)).all()
        counts: dict[str, int] = {s.value: 0 for s in LeadStatus}
        for status, count in rows:
            counts[status.value] = count

        stages = [s.value for s in _FUNNEL_ORDER]
        conversions: list[dict[str, Any]] = []
        for i in range(len(stages) - 1):
            here = counts.get(stages[i], 0)
            nxt = counts.get(stages[i + 1], 0)
            rate = (nxt / here) if here > 0 else 0.0
            conversions.append(
                {"from": stages[i], "to": stages[i + 1], "rate": round(rate, 3)}
            )

        return {"counts": counts, "conversions": conversions}

    async def get_pipeline(
        self,
        owner: str | None = None,
        stage: str | None = None,
        limit: int = 100,
    ) -> list[Lead]:
        """Return the active pipeline (non-archived/lost) filtered by owner/stage."""
        query = select(Lead).where(
            Lead.status.notin_([LeadStatus.LOST, LeadStatus.ARCHIVED])
        )
        if owner:
            query = query.where(Lead.assigned_to == owner)
        if stage:
            query = query.where(Lead.status == LeadStatus(stage))
        query = query.order_by(Lead.updated_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
