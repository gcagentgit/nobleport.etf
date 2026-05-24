"""
NoblePort Notification Service

Routes notifications across channels: in-app, email, SMS, webhook.
Supports priority escalation and agent-originated alerts.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notification import (
    Notification,
    NotificationCategory,
    NotificationChannel,
    NotificationPriority,
)

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    async def send(
        db: AsyncSession,
        recipient: str,
        title: str,
        category: NotificationCategory,
        *,
        body: str | None = None,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        sender: str = "system",
        agent: str | None = None,
        subject_type: str | None = None,
        subject_id: str | None = None,
        action_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Notification:
        notification = Notification(
            channel=channel,
            priority=priority,
            category=category,
            recipient=recipient,
            sender=sender,
            agent=agent,
            title=title,
            body=body,
            subject_type=subject_type,
            subject_id=subject_id,
            action_url=action_url,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        logger.info(
            "Notification [%s] -> %s: %s",
            priority.value, recipient, title,
        )
        return notification

    @staticmethod
    async def mark_read(
        notification_id: str, db: AsyncSession
    ) -> None:
        await db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(read=True, read_at=datetime.now(timezone.utc))
        )
        await db.commit()

    @staticmethod
    async def get_unread(
        recipient: str, db: AsyncSession, limit: int = 50
    ) -> list[Notification]:
        result = await db.execute(
            select(Notification)
            .where(Notification.recipient == recipient, Notification.read == False)  # noqa: E712
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_unread_count(
        recipient: str, db: AsyncSession
    ) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.recipient == recipient, Notification.read == False)  # noqa: E712
        )
        return result.scalar() or 0

    @staticmethod
    async def escalate(
        db: AsyncSession,
        original_id: str,
        escalate_to: str,
    ) -> Notification:
        result = await db.execute(
            select(Notification).where(Notification.id == original_id)
        )
        original = result.scalar_one_or_none()
        if not original:
            raise ValueError(f"Notification {original_id} not found")

        return await NotificationService.send(
            db,
            recipient=escalate_to,
            title=f"[ESCALATED] {original.title}",
            category=NotificationCategory.ESCALATION,
            body=original.body,
            channel=NotificationChannel.IN_APP,
            priority=NotificationPriority.CRITICAL,
            sender="system",
            subject_type=original.subject_type,
            subject_id=original.subject_id,
            action_url=original.action_url,
            metadata={"escalated_from": original.id},
        )
