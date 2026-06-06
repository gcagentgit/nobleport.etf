"""
NoblePort Contacts API

CRM contact directory endpoints.
"""

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.domains.contacts.service import ContactsService

router = APIRouter()


def _contact_dict(c) -> dict:
    return {
        "id": c.id,
        "first_name": c.first_name,
        "last_name": c.last_name,
        "company": c.company,
        "email": c.email,
        "phone": c.phone,
        "role": c.role,
        "source": c.source,
        "tags": c.tags,
        "do_not_contact": c.do_not_contact,
        "dnc_reason": c.dnc_reason,
        "notes": c.notes,
        "hubspot_id": c.hubspot_id,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _interaction_dict(i) -> dict:
    return {
        "id": i.id,
        "contact_id": i.contact_id,
        "interaction_type": i.interaction_type.value,
        "direction": i.direction.value,
        "summary": i.summary,
        "full_content": i.full_content,
        "occurred_at": i.occurred_at.isoformat() if i.occurred_at else None,
        "recorded_by": i.recorded_by,
        "related_lead_id": i.related_lead_id,
        "related_job_id": i.related_job_id,
    }


@router.get("/contacts")
async def list_contacts(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    service = ContactsService(db)
    return [_contact_dict(c) for c in await service.list_contacts(limit=limit)]


@router.get("/contacts/{contact_id}")
async def get_contact(contact_id: str, db: AsyncSession = Depends(get_db)):
    service = ContactsService(db)
    try:
        return _contact_dict(await service.get(contact_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/contacts", status_code=201)
async def create_contact(
    fields: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = ContactsService(db)
    contact = await service.create_contact(**fields)
    return _contact_dict(contact)


@router.patch("/contacts/{contact_id}")
async def update_contact(
    contact_id: str,
    updates: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = ContactsService(db)
    try:
        return _contact_dict(await service.update(contact_id, updates))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/contacts/{contact_id}/history")
async def history(contact_id: str, db: AsyncSession = Depends(get_db)):
    service = ContactsService(db)
    try:
        return [_interaction_dict(i) for i in await service.get_history(contact_id)]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/contacts/{contact_id}/interactions", status_code=201)
async def log_interaction(
    contact_id: str,
    interaction_type: str = Body(...),
    direction: str = Body(...),
    summary: str | None = Body(None),
    full_content: str | None = Body(None),
    recorded_by: str | None = Body(None),
    related_lead_id: str | None = Body(None),
    related_job_id: str | None = Body(None),
    db: AsyncSession = Depends(get_db),
):
    service = ContactsService(db)
    try:
        interaction = await service.log_interaction(
            contact_id=contact_id,
            interaction_type=interaction_type,
            direction=direction,
            summary=summary,
            full_content=full_content,
            recorded_by=recorded_by,
            related_lead_id=related_lead_id,
            related_job_id=related_job_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _interaction_dict(interaction)


@router.post("/contacts/{contact_id}/dnc")
async def mark_dnc(
    contact_id: str,
    reason: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    service = ContactsService(db)
    try:
        return _contact_dict(await service.mark_dnc(contact_id, reason))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/merge")
async def merge(
    primary_id: str = Body(...),
    duplicate_id: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = ContactsService(db)
    try:
        return _contact_dict(await service.merge_duplicates(primary_id, duplicate_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    service = ContactsService(db)
    return [_contact_dict(c) for c in await service.search(q, limit=limit)]
