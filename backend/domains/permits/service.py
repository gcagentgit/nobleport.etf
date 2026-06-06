"""
NoblePort Permits Service

Permit lifecycle: submit -> corrections -> issued, and inspection
scheduling/results.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.inspection import Inspection, InspectionStatus
from backend.models.permit import Permit, PermitStatus, PermitType


class PermitsService:
    """Service for permit applications, AHJ tracking, and inspections."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_permit(self, permit_id: str) -> Permit:
        result = await self.db.execute(select(Permit).where(Permit.id == permit_id))
        permit = result.scalar_one_or_none()
        if not permit:
            raise ValueError(f"Permit {permit_id} not found")
        return permit

    async def _get_inspection(self, inspection_id: str) -> Inspection:
        result = await self.db.execute(
            select(Inspection).where(Inspection.id == inspection_id)
        )
        inspection = result.scalar_one_or_none()
        if not inspection:
            raise ValueError(f"Inspection {inspection_id} not found")
        return inspection

    async def submit_permit(
        self,
        job_id: str,
        permit_type: PermitType,
        ahj: str,
        reviewer: str | None = None,
        estimated_review_days: int | None = None,
        fee_amount: float | None = None,
        notes: str | None = None,
    ) -> Permit:
        """Create a permit application and transition it to submitted."""
        permit = Permit(
            job_id=job_id,
            ahj=ahj,
            permit_type=permit_type,
            status=PermitStatus.SUBMITTED,
            submitted_at=datetime.now(timezone.utc),
            reviewer=reviewer,
            estimated_review_days=estimated_review_days,
            fee_amount=fee_amount,
            notes=notes,
        )
        self.db.add(permit)
        await self.db.commit()
        await self.db.refresh(permit)
        return permit

    async def record_correction(self, permit_id: str, correction: str) -> Permit:
        """Record a correction cycle from the AHJ and bump the counter."""
        permit = await self._get_permit(permit_id)
        permit.status = PermitStatus.CORRECTIONS
        permit.corrections_count = (permit.corrections_count or 0) + 1

        stamp = datetime.now(timezone.utc).isoformat()
        line = f"[correction {permit.corrections_count} {stamp}] {correction}"
        permit.notes = f"{permit.notes}\n{line}" if permit.notes else line

        await self.db.commit()
        await self.db.refresh(permit)
        return permit

    async def record_issuance(
        self,
        permit_id: str,
        permit_number: str,
        issued_at: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> Permit:
        """Mark a permit as issued and record its number + expiration."""
        permit = await self._get_permit(permit_id)
        permit.permit_number = permit_number
        permit.status = PermitStatus.ISSUED
        permit.issued_at = issued_at or datetime.now(timezone.utc)
        if expires_at is not None:
            permit.expires_at = expires_at

        if permit.submitted_at and permit.issued_at:
            try:
                submitted = (
                    permit.submitted_at
                    if isinstance(permit.submitted_at, datetime)
                    else datetime.fromisoformat(str(permit.submitted_at))
                )
                issued = (
                    permit.issued_at
                    if isinstance(permit.issued_at, datetime)
                    else datetime.fromisoformat(str(permit.issued_at))
                )
                permit.actual_review_days = (issued - submitted).days
            except (TypeError, ValueError):
                pass

        await self.db.commit()
        await self.db.refresh(permit)
        return permit

    async def schedule_inspection(
        self,
        permit_id: str,
        inspection_type: str,
        scheduled_at: datetime,
        inspector: str | None = None,
    ) -> Inspection:
        """Schedule a required inspection against a permit."""
        permit = await self._get_permit(permit_id)
        inspection = Inspection(
            permit_id=permit.id,
            job_id=permit.job_id,
            inspection_type=inspection_type,
            status=InspectionStatus.SCHEDULED,
            scheduled_at=scheduled_at,
            inspector=inspector,
        )
        self.db.add(inspection)
        await self.db.commit()
        await self.db.refresh(inspection)
        return inspection

    async def record_inspection_result(
        self,
        inspection_id: str,
        passed: bool,
        notes: str | None = None,
        corrections_required: str | None = None,
    ) -> Inspection:
        """Record pass/fail outcome and flag re-inspection if needed."""
        inspection = await self._get_inspection(inspection_id)
        inspection.status = (
            InspectionStatus.PASSED if passed else InspectionStatus.FAILED
        )
        inspection.completed_at = datetime.now(timezone.utc)
        inspection.result_notes = notes
        if corrections_required:
            inspection.corrections_required = corrections_required
            inspection.reinspection_needed = True
        elif not passed:
            inspection.reinspection_needed = True

        await self.db.commit()
        await self.db.refresh(inspection)
        return inspection

    async def get_open_permits(self, ahj: str | None = None) -> list[Permit]:
        """Return all permits not yet issued / not denied / not expired."""
        open_statuses = [
            PermitStatus.INTAKE,
            PermitStatus.SUBMITTED,
            PermitStatus.REVIEW,
            PermitStatus.CORRECTIONS,
        ]
        query = select(Permit).where(Permit.status.in_(open_statuses))
        if ahj:
            query = query.where(Permit.ahj == ahj)
        query = query.order_by(Permit.submitted_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_pending_inspections(self, window_days: int = 7) -> list[Inspection]:
        """Return inspections scheduled within the next `window_days` days."""
        now = datetime.now(timezone.utc)
        horizon = now + timedelta(days=window_days)
        query = (
            select(Inspection)
            .where(
                Inspection.status.in_(
                    [InspectionStatus.SCHEDULED, InspectionStatus.REQUESTED]
                ),
                Inspection.scheduled_at <= horizon,
            )
            .order_by(Inspection.scheduled_at.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_permit(self, permit_id: str) -> Permit:
        return await self._get_permit(permit_id)

    async def get_permits_by_ahj(self, ahj: str) -> list[Permit]:
        result = await self.db.execute(
            select(Permit)
            .where(Permit.ahj == ahj)
            .order_by(Permit.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def permit_to_dict(permit: Permit) -> dict[str, Any]:
        return {
            "id": permit.id,
            "permit_number": permit.permit_number,
            "job_id": permit.job_id,
            "ahj": permit.ahj,
            "permit_type": permit.permit_type.value,
            "status": permit.status.value,
            "submitted_at": permit.submitted_at,
            "issued_at": permit.issued_at,
            "expires_at": permit.expires_at,
            "corrections_count": permit.corrections_count,
            "reviewer": permit.reviewer,
            "fee_amount": permit.fee_amount,
            "fee_paid": permit.fee_paid,
        }

    @staticmethod
    def inspection_to_dict(inspection: Inspection) -> dict[str, Any]:
        return {
            "id": inspection.id,
            "permit_id": inspection.permit_id,
            "job_id": inspection.job_id,
            "inspection_type": inspection.inspection_type,
            "status": inspection.status.value,
            "scheduled_at": inspection.scheduled_at,
            "completed_at": inspection.completed_at,
            "inspector": inspection.inspector,
            "reinspection_needed": inspection.reinspection_needed,
            "result_notes": inspection.result_notes,
        }
