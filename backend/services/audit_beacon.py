"""
AuditBeacon Service — Immutable Operational Truth

Every operational mutation flows through here. Each entry is hash-linked
to its predecessor, creating a tamper-evident chain. This is the core of
NoblePort's trust infrastructure.

NO autonomous authority. All treasury, contract, compliance, and execution-risk
actions require human approval gates before audit commitment.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.audit_entry import (
    ApprovalType,
    AuditAction,
    AuditEntry,
    AuditStatus,
)

logger = logging.getLogger(__name__)

GENESIS_HASH = "0" * 64


class AuditBeacon:

    @staticmethod
    def _compute_hash(
        prev_hash: str,
        timestamp: str,
        operator: str,
        action: str,
        subject_type: str,
        subject_id: str,
        detail: str | None,
    ) -> str:
        payload = f"{prev_hash}|{timestamp}|{operator}|{action}|{subject_type}|{subject_id}|{detail or ''}"
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    async def _get_prev_hash(db: AsyncSession) -> str:
        result = await db.execute(
            select(AuditEntry.entry_hash)
            .order_by(AuditEntry.created_at.desc())
            .limit(1)
        )
        prev = result.scalar_one_or_none()
        return prev or GENESIS_HASH

    @classmethod
    async def record(
        cls,
        db: AsyncSession,
        operator: str,
        action: AuditAction,
        subject_type: str,
        subject_id: str,
        *,
        agent: str | None = None,
        subject_label: str | None = None,
        approval: ApprovalType = ApprovalType.AUTO,
        detail: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        now = datetime.now(timezone.utc)
        ts_str = now.isoformat()

        prev_hash = await cls._get_prev_hash(db)
        entry_hash = cls._compute_hash(
            prev_hash, ts_str, operator, action.value,
            subject_type, subject_id, detail,
        )

        entry = AuditEntry(
            timestamp=now,
            operator=operator,
            agent=agent,
            action=action,
            subject_type=subject_type,
            subject_id=subject_id,
            subject_label=subject_label,
            approval=approval,
            entry_hash=entry_hash,
            prev_hash=prev_hash,
            status=AuditStatus.COMMITTED,
            detail=detail,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(entry)
        await db.flush()

        logger.info(
            "AuditBeacon: %s %s/%s by %s [%s] hash=%s",
            action.value, subject_type, subject_id,
            operator, approval.value, entry_hash[:12],
        )
        return entry

    @staticmethod
    async def verify_chain(db: AsyncSession, limit: int = 100) -> dict[str, Any]:
        result = await db.execute(
            select(AuditEntry)
            .order_by(AuditEntry.created_at.asc())
            .limit(limit)
        )
        entries = result.scalars().all()

        if not entries:
            return {"valid": True, "checked": 0, "errors": []}

        errors = []
        for i, entry in enumerate(entries):
            if i == 0:
                if entry.prev_hash != GENESIS_HASH:
                    first_result = await db.execute(
                        select(AuditEntry)
                        .where(AuditEntry.entry_hash == entry.prev_hash)
                    )
                    if not first_result.scalar_one_or_none():
                        pass  # Could be a truncated chain
            else:
                if entry.prev_hash != entries[i - 1].entry_hash:
                    errors.append({
                        "index": i,
                        "entry_id": entry.id,
                        "expected_prev": entries[i - 1].entry_hash,
                        "actual_prev": entry.prev_hash,
                    })

            expected = AuditBeacon._compute_hash(
                entry.prev_hash,
                entry.timestamp.isoformat() if isinstance(entry.timestamp, datetime) else entry.timestamp,
                entry.operator,
                entry.action.value,
                entry.subject_type,
                entry.subject_id,
                entry.detail,
            )
            if expected != entry.entry_hash:
                errors.append({
                    "index": i,
                    "entry_id": entry.id,
                    "issue": "hash_mismatch",
                    "expected": expected,
                    "actual": entry.entry_hash,
                })

        return {
            "valid": len(errors) == 0,
            "checked": len(entries),
            "errors": errors,
        }

    @staticmethod
    async def get_trail(
        db: AsyncSession,
        subject_type: str | None = None,
        subject_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEntry]:
        query = select(AuditEntry).order_by(AuditEntry.timestamp.desc())

        if subject_type:
            query = query.where(AuditEntry.subject_type == subject_type)
        if subject_id:
            query = query.where(AuditEntry.subject_id == subject_id)

        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
