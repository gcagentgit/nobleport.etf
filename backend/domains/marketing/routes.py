"""
NoblePort Marketing API

Endpoints for campaigns, spend, channel performance, and attribution.
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.domains.marketing.service import MarketingService

router = APIRouter()


def _campaign_dict(c) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "channel": c.channel.value,
        "status": c.status.value,
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "budget": c.budget,
        "spent": c.spent,
        "target_audience": c.target_audience,
        "goals": c.goals,
        "utm_source": c.utm_source,
        "utm_medium": c.utm_medium,
        "utm_campaign": c.utm_campaign,
    }


@router.get("/campaigns")
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    service = MarketingService(db)
    return [_campaign_dict(c) for c in await service.list_campaigns()]


@router.post("/campaigns", status_code=201)
async def create_campaign(
    name: str = Body(...),
    channel: str = Body(...),
    budget: float = Body(0.0),
    start_date: date | None = Body(None),
    end_date: date | None = Body(None),
    target_audience: str | None = Body(None),
    goals: dict[str, Any] | None = Body(None),
    utm_source: str | None = Body(None),
    utm_medium: str | None = Body(None),
    utm_campaign: str | None = Body(None),
    db: AsyncSession = Depends(get_db),
):
    service = MarketingService(db)
    try:
        campaign = await service.create_campaign(
            name=name,
            channel=channel,
            budget=budget,
            start_date=start_date,
            end_date=end_date,
            target_audience=target_audience,
            goals=goals,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _campaign_dict(campaign)


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    service = MarketingService(db)
    try:
        return _campaign_dict(await service.get_campaign(campaign_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    updates: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = MarketingService(db)
    try:
        return _campaign_dict(await service.update_campaign(campaign_id, updates))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    service = MarketingService(db)
    try:
        return _campaign_dict(await service.pause_campaign(campaign_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/campaigns/{campaign_id}/spend")
async def record_spend(
    campaign_id: str,
    amount: float = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    service = MarketingService(db)
    try:
        return _campaign_dict(await service.record_spend(campaign_id, amount))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/campaigns/{campaign_id}/roi")
async def campaign_roi(campaign_id: str, db: AsyncSession = Depends(get_db)):
    service = MarketingService(db)
    try:
        return await service.get_campaign_roi(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/attribute")
async def attribute_lead(
    lead_id: str = Body(...),
    utm_params: dict[str, str] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = MarketingService(db)
    try:
        attribution = await service.attribute_lead(lead_id, utm_params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if attribution is None:
        return {"matched": False}
    return {
        "matched": True,
        "attribution_id": attribution.id,
        "campaign_id": attribution.campaign_id,
        "touch_type": attribution.touch_type.value,
    }


@router.get("/channels/performance")
async def channel_performance(
    start: date | None = Query(None),
    end: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = MarketingService(db)
    return await service.get_channel_performance(start=start, end=end)


@router.get("/attribution")
async def attribution_summary(db: AsyncSession = Depends(get_db)):
    service = MarketingService(db)
    return await service.get_attribution_summary()
