"""
NoblePort Follow-Ups Service

Drives sequences, steps, and instances through their lifecycle.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.follow_ups.models import (
    FollowUpChannel,
    FollowUpInstance,
    FollowUpInstanceStatus,
    FollowUpSequence,
    FollowUpStep,
)


class FollowUpService:
    """Sequence lifecycle + step delivery."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Sequences
    # ------------------------------------------------------------------
    async def create_sequence(
        self,
        name: str,
        steps: list[dict[str, Any]],
        description: str | None = None,
        trigger_event: str | None = None,
    ) -> FollowUpSequence:
        sequence = FollowUpSequence(
            name=name,
            description=description,
            trigger_event=trigger_event,
            active=True,
        )
        self.db.add(sequence)
        await self.db.flush()  # need sequence.id

        for idx, step_data in enumerate(steps, start=1):
            step = FollowUpStep(
                sequence_id=sequence.id,
                step_number=step_data.get("step_number", idx),
                delay_days=step_data.get("delay_days", 0),
                channel=FollowUpChannel(step_data["channel"]),
                subject=step_data.get("subject"),
                body_template=step_data.get("body_template"),
                condition=step_data.get("condition"),
            )
            self.db.add(step)

        await self.db.commit()
        await self.db.refresh(sequence)
        return sequence

    async def list_sequences(self) -> list[FollowUpSequence]:
        result = await self.db.execute(select(FollowUpSequence))
        return list(result.scalars().all())

    async def _get_first_step(self, sequence_id: str) -> FollowUpStep | None:
        stmt = (
            select(FollowUpStep)
            .where(FollowUpStep.sequence_id == sequence_id)
            .order_by(FollowUpStep.step_number.asc())
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def _get_step(self, sequence_id: str, step_number: int) -> FollowUpStep | None:
        stmt = select(FollowUpStep).where(
            FollowUpStep.sequence_id == sequence_id,
            FollowUpStep.step_number == step_number,
        )
        return (await self.db.execute(stmt)).scalars().first()

    # ------------------------------------------------------------------
    # Instances
    # ------------------------------------------------------------------
    async def start_sequence(
        self, sequence_id: str, target: dict[str, str]
    ) -> FollowUpInstance:
        """Start an instance against a contact / lead / job (target dict keys)."""
        sequence = await self.db.get(FollowUpSequence, sequence_id)
        if not sequence:
            raise ValueError(f"Sequence {sequence_id} not found")
        if not sequence.active:
            raise ValueError(f"Sequence {sequence_id} is not active")

        first = await self._get_first_step(sequence_id)
        now = datetime.now(timezone.utc)
        next_send = now + timedelta(days=first.delay_days) if first else None

        instance = FollowUpInstance(
            sequence_id=sequence_id,
            contact_id=target.get("contact_id"),
            lead_id=target.get("lead_id"),
            job_id=target.get("job_id"),
            current_step=0,
            status=FollowUpInstanceStatus.ACTIVE,
            started_at=now,
            next_send_at=next_send,
        )
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def cancel_instance(self, instance_id: str) -> FollowUpInstance:
        instance = await self._get_instance(instance_id)
        instance.status = FollowUpInstanceStatus.CANCELLED
        instance.next_send_at = None
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def pause_instance(self, instance_id: str) -> FollowUpInstance:
        instance = await self._get_instance(instance_id)
        instance.status = FollowUpInstanceStatus.PAUSED
        instance.next_send_at = None
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def record_response(
        self, instance_id: str, response: str
    ) -> FollowUpInstance:
        """A reply was received — pause the instance and record what came back."""
        instance = await self._get_instance(instance_id)
        instance.last_response = response
        instance.status = FollowUpInstanceStatus.PAUSED
        instance.next_send_at = None
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def process_due(self) -> dict[str, Any]:
        """Find all instances with next_send_at in the past and advance them."""
        now = datetime.now(timezone.utc)
        stmt = select(FollowUpInstance).where(
            FollowUpInstance.status == FollowUpInstanceStatus.ACTIVE,
            FollowUpInstance.next_send_at.is_not(None),
            FollowUpInstance.next_send_at <= now,
        )
        due = list((await self.db.execute(stmt)).scalars().all())

        processed: list[str] = []
        completed: list[str] = []

        for instance in due:
            next_step_number = instance.current_step + 1
            step = await self._get_step(instance.sequence_id, next_step_number)
            if step is None:
                # No more steps -> complete
                instance.status = FollowUpInstanceStatus.COMPLETED
                instance.completed_at = now
                instance.next_send_at = None
                completed.append(instance.id)
                continue

            # "Send" the step. Real delivery would dispatch to email/SMS workers.
            instance.current_step = next_step_number
            processed.append(instance.id)

            follow = await self._get_step(instance.sequence_id, next_step_number + 1)
            if follow:
                instance.next_send_at = now + timedelta(days=follow.delay_days)
            else:
                instance.status = FollowUpInstanceStatus.COMPLETED
                instance.completed_at = now
                instance.next_send_at = None
                completed.append(instance.id)

        await self.db.commit()
        return {
            "checked": len(due),
            "advanced": processed,
            "completed": completed,
        }

    async def list_instances(
        self, status: str | None = None
    ) -> list[FollowUpInstance]:
        query = select(FollowUpInstance).order_by(FollowUpInstance.created_at.desc())
        if status:
            query = query.where(
                FollowUpInstance.status == FollowUpInstanceStatus(status)
            )
        result = await self.db.execute(query.limit(200))
        return list(result.scalars().all())

    async def due_soon(self, hours: int = 24) -> list[FollowUpInstance]:
        cutoff = datetime.now(timezone.utc) + timedelta(hours=hours)
        stmt = (
            select(FollowUpInstance)
            .where(
                FollowUpInstance.status == FollowUpInstanceStatus.ACTIVE,
                FollowUpInstance.next_send_at.is_not(None),
                FollowUpInstance.next_send_at <= cutoff,
            )
            .order_by(FollowUpInstance.next_send_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_instance(self, instance_id: str) -> FollowUpInstance:
        instance = await self.db.get(FollowUpInstance, instance_id)
        if not instance:
            raise ValueError(f"Follow-up instance {instance_id} not found")
        return instance
