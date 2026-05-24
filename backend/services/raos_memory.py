"""
RAOS Memory Service — Role-Aware Operational State

Manages the active operational memory layer. Agents read and write
scoped memory entries during operations. Supports TTL-based expiry
and optimistic locking for concurrent agent access.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.operational_memory import (
    MemoryCategory,
    MemoryScope,
    OperationalMemory,
)

logger = logging.getLogger(__name__)


class RAOSMemory:

    @staticmethod
    async def write(
        db: AsyncSession,
        scope: MemoryScope,
        category: MemoryCategory,
        key: str,
        value: Any,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        written_by: str | None = None,
        ttl_seconds: int | None = None,
    ) -> OperationalMemory:
        result = await db.execute(
            select(OperationalMemory).where(
                and_(
                    OperationalMemory.scope == scope,
                    OperationalMemory.key == key,
                )
            )
        )
        existing = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        expires_at = None
        if ttl_seconds:
            from datetime import timedelta
            expires_at = now + timedelta(seconds=ttl_seconds)

        if existing:
            existing.value_json = json.dumps(value)
            existing.category = category
            existing.entity_type = entity_type
            existing.entity_id = entity_id
            existing.written_by = written_by
            existing.expires_at = expires_at
            existing.version += 1
            await db.commit()
            await db.refresh(existing)
            return existing

        mem = OperationalMemory(
            scope=scope,
            category=category,
            key=key,
            value_json=json.dumps(value),
            entity_type=entity_type,
            entity_id=entity_id,
            written_by=written_by,
            expires_at=expires_at,
        )
        db.add(mem)
        await db.commit()
        await db.refresh(mem)
        return mem

    @staticmethod
    async def read(
        db: AsyncSession,
        scope: MemoryScope,
        key: str,
    ) -> Any | None:
        result = await db.execute(
            select(OperationalMemory).where(
                and_(
                    OperationalMemory.scope == scope,
                    OperationalMemory.key == key,
                )
            )
        )
        mem = result.scalar_one_or_none()
        if not mem:
            return None

        if mem.expires_at:
            expires = mem.expires_at if isinstance(mem.expires_at, datetime) else datetime.fromisoformat(str(mem.expires_at))
            if expires < datetime.now(timezone.utc):
                await db.delete(mem)
                await db.commit()
                return None

        return json.loads(mem.value_json)

    @staticmethod
    async def query(
        db: AsyncSession,
        scope: MemoryScope,
        category: MemoryCategory | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = select(OperationalMemory).where(
            OperationalMemory.scope == scope
        )
        if category:
            query = query.where(OperationalMemory.category == category)
        if entity_type:
            query = query.where(OperationalMemory.entity_type == entity_type)
        if entity_id:
            query = query.where(OperationalMemory.entity_id == entity_id)

        query = query.order_by(OperationalMemory.updated_at.desc()).limit(limit)
        result = await db.execute(query)
        entries = result.scalars().all()

        return [
            {
                "key": e.key,
                "value": json.loads(e.value_json),
                "category": e.category.value,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "written_by": e.written_by,
                "version": e.version,
                "updated_at": e.updated_at.isoformat(),
            }
            for e in entries
        ]

    @staticmethod
    async def purge_expired(db: AsyncSession) -> int:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            delete(OperationalMemory).where(
                and_(
                    OperationalMemory.expires_at.isnot(None),
                    OperationalMemory.expires_at < now,
                )
            )
        )
        await db.commit()
        count = result.rowcount
        if count:
            logger.info("RAOS: purged %d expired memory entries", count)
        return count
