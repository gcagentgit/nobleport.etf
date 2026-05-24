"""
AuditBeacon API — Immutable Audit Trail Endpoints

Provides read access to the immutable audit chain and chain
verification. Write access is internal-only (services record
audit entries as side-effects of operational mutations).
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.services.audit_beacon import AuditBeacon

router = APIRouter()


class AuditEntryResponse(BaseModel):
    id: str
    timestamp: str
    operator: str
    agent: str | None
    action: str
    subject_type: str
    subject_id: str
    subject_label: str | None
    approval: str
    entry_hash: str
    prev_hash: str
    anchor_tx: str | None
    status: str
    detail: str | None
    verified: bool
    created_at: str

    model_config = {"from_attributes": True}


@router.get("/trail")
async def get_audit_trail(
    subject_type: str | None = Query(default=None),
    subject_id: str | None = Query(default=None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    entries = await AuditBeacon.get_trail(
        db, subject_type=subject_type, subject_id=subject_id,
        limit=limit, offset=offset,
    )
    return {
        "items": [AuditEntryResponse.model_validate(e) for e in entries],
        "limit": limit,
        "offset": offset,
    }


@router.get("/verify")
async def verify_chain(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    return await AuditBeacon.verify_chain(db, limit=limit)
