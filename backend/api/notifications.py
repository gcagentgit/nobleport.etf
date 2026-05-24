"""
Notification API — System Notification Endpoints

Read and manage notifications for operators. Supports
mark-as-read, unread counts, and escalation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.models.notification import (
    Notification,
    NotificationCategory,
    NotificationChannel,
    NotificationPriority,
)
from backend.services.notification_service import NotificationService

router = APIRouter()


class NotificationResponse(BaseModel):
    id: str
    channel: str
    priority: str
    category: str
    recipient: str
    sender: str
    agent: str | None
    title: str
    body: str | None
    subject_type: str | None
    subject_id: str | None
    read: bool
    action_url: str | None
    created_at: str

    model_config = {"from_attributes": True}


class NotificationSend(BaseModel):
    recipient: str
    title: str
    category: str
    body: str | None = None
    channel: str = "in_app"
    priority: str = "normal"
    subject_type: str | None = None
    subject_id: str | None = None
    action_url: str | None = None


@router.get("")
async def list_notifications(
    recipient: str = Query(...),
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Notification).where(Notification.recipient == recipient)
    if unread_only:
        query = query.where(Notification.read == False)  # noqa: E712

    query = query.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    unread_count = await NotificationService.get_unread_count(recipient, db)

    return {
        "items": [NotificationResponse.model_validate(n) for n in items],
        "unread_count": unread_count,
    }


@router.post("", response_model=NotificationResponse)
async def send_notification(
    data: NotificationSend, db: AsyncSession = Depends(get_db)
):
    notification = await NotificationService.send(
        db,
        recipient=data.recipient,
        title=data.title,
        category=NotificationCategory(data.category),
        body=data.body,
        channel=NotificationChannel(data.channel),
        priority=NotificationPriority(data.priority),
        subject_type=data.subject_type,
        subject_id=data.subject_id,
        action_url=data.action_url,
    )
    return NotificationResponse.model_validate(notification)


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str, db: AsyncSession = Depends(get_db)
):
    await NotificationService.mark_read(notification_id, db)
    return {"status": "ok"}


@router.post("/{notification_id}/escalate")
async def escalate_notification(
    notification_id: str,
    escalate_to: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        escalated = await NotificationService.escalate(db, notification_id, escalate_to)
        return NotificationResponse.model_validate(escalated)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
