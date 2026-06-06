"""
NoblePort Jobs Service

Business logic for active job execution: kickoff, progress, change orders,
profitability, at-risk flags, and closeout.
"""

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.change_order import (
    ChangeOrder,
    ChangeOrderReason,
    ChangeOrderStatus,
)
from backend.models.job import Job, JobStatus


class JobsService:
    """Service for managing active jobs through their execution lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_job(self, job_id: str) -> Job:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        return job

    async def kickoff(
        self,
        job_id: str,
        project_manager: str | None = None,
        crew: str | None = None,
        start_date: date | None = None,
    ) -> Job:
        """Move a job into active execution. Requires deposit gate passed."""
        job = await self._get_job(job_id)

        if not job.deposit_gate_passed:
            raise ValueError(
                f"Cannot kickoff job {job.job_number}: deposit gate not passed "
                f"({job.deposit_paid} of {job.deposit_required} paid)"
            )

        job.status = JobStatus.IN_PROGRESS
        if crew is not None:
            job.crew = crew
        if start_date is not None:
            job.start_date = start_date
        if project_manager and job.notes:
            job.notes = f"{job.notes}\nPM: {project_manager}"
        elif project_manager:
            job.notes = f"PM: {project_manager}"

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def update_progress(self, job_id: str, percent_complete: float) -> Job:
        """Update job progress and auto-transition near-complete jobs to punch list."""
        if percent_complete < 0 or percent_complete > 100:
            raise ValueError("percent_complete must be between 0 and 100")

        job = await self._get_job(job_id)

        # Stash percent in notes for now; dedicated field can be added later.
        progress_line = f"[progress] {datetime.now(timezone.utc).isoformat()} {percent_complete:.1f}%"
        job.notes = f"{job.notes}\n{progress_line}" if job.notes else progress_line

        if percent_complete >= 100 and job.status == JobStatus.IN_PROGRESS:
            job.status = JobStatus.PUNCH_LIST
        elif percent_complete >= 95 and job.status == JobStatus.IN_PROGRESS:
            job.status = JobStatus.PUNCH_LIST

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def forecast_completion(self, job_id: str) -> dict[str, Any]:
        """Forecast completion based on current progress and schedule.

        This is the integration point for the GCagent forecasting logic.
        Returns a structured projection rather than mutating the job.
        """
        job = await self._get_job(job_id)

        forecast: dict[str, Any] = {
            "job_id": job.id,
            "job_number": job.job_number,
            "status": job.status.value,
            "estimated_end_date": job.estimated_end_date,
            "actual_end_date": job.actual_end_date,
            "on_track": True,
            "projected_end_date": job.estimated_end_date,
            "confidence": "medium",
        }

        if job.actual_end_date:
            forecast["on_track"] = True
            forecast["confidence"] = "complete"
            return forecast

        if job.status in (JobStatus.ON_HOLD, JobStatus.CANCELLED):
            forecast["on_track"] = False
            forecast["confidence"] = "low"

        return forecast

    async def add_change_order(
        self,
        job_id: str,
        title: str,
        labor_cost: float = 0.0,
        material_cost: float = 0.0,
        markup_percent: float = 20.0,
        reason: ChangeOrderReason = ChangeOrderReason.CLIENT_REQUEST,
        description: str | None = None,
    ) -> ChangeOrder:
        """Create a change order against a job and update the job rollup."""
        job = await self._get_job(job_id)

        # Sequence + number
        count_result = await self.db.execute(
            select(func.count(ChangeOrder.id)).where(ChangeOrder.job_id == job_id)
        )
        existing = count_result.scalar() or 0
        sequence = existing + 1

        subtotal = labor_cost + material_cost
        markup_amount = subtotal * (markup_percent / 100.0)
        total_amount = subtotal + markup_amount

        co = ChangeOrder(
            job_id=job_id,
            change_order_number=f"{job.job_number}-CO-{sequence:03d}",
            sequence=sequence,
            status=ChangeOrderStatus.DRAFT,
            title=title,
            description=description,
            reason=reason,
            labor_cost=labor_cost,
            material_cost=material_cost,
            markup_percent=markup_percent,
            markup_amount=markup_amount,
            total_amount=total_amount,
        )
        self.db.add(co)

        job.change_order_count = sequence
        job.change_order_total = (job.change_order_total or 0.0) + total_amount

        await self.db.commit()
        await self.db.refresh(co)
        return co

    async def get_profitability(self, job_id: str) -> dict[str, Any]:
        """Compute live profitability snapshot for a job."""
        job = await self._get_job(job_id)

        # Pull approved/in-progress change orders for a true revenue picture.
        result = await self.db.execute(
            select(func.coalesce(func.sum(ChangeOrder.total_amount), 0.0)).where(
                ChangeOrder.job_id == job_id,
                ChangeOrder.status.in_(
                    [
                        ChangeOrderStatus.APPROVED,
                        ChangeOrderStatus.IN_PROGRESS,
                        ChangeOrderStatus.COMPLETED,
                    ]
                ),
            )
        )
        approved_awo = float(result.scalar() or 0.0)

        revenue = (job.contract_value or 0.0) + approved_awo
        costs = job.total_costs or 0.0
        margin = revenue - costs
        margin_percent = (margin / revenue * 100.0) if revenue else 0.0

        return {
            "job_id": job.id,
            "job_number": job.job_number,
            "contract_value": job.contract_value,
            "approved_change_orders": approved_awo,
            "total_revenue": revenue,
            "total_costs": costs,
            "margin": margin,
            "margin_percent": margin_percent,
            "total_invoiced": job.total_invoiced,
            "total_paid": job.total_paid,
        }

    async def flag_at_risk(self, job_id: str, reason: str) -> Job:
        """Flag a job as at-risk. Currently captured via on_hold + notes."""
        job = await self._get_job(job_id)
        stamp = datetime.now(timezone.utc).isoformat()
        flag_line = f"[at-risk {stamp}] {reason}"
        job.notes = f"{job.notes}\n{flag_line}" if job.notes else flag_line

        if job.status == JobStatus.IN_PROGRESS:
            job.status = JobStatus.ON_HOLD

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_active_jobs(
        self, status: JobStatus | None = None, limit: int = 100
    ) -> list[Job]:
        """List active jobs, optionally filtered by status."""
        active_statuses = [
            JobStatus.SCHEDULED,
            JobStatus.IN_PROGRESS,
            JobStatus.ON_HOLD,
            JobStatus.PUNCH_LIST,
        ]
        query = select(Job)
        if status is not None:
            query = query.where(Job.status == status)
        else:
            query = query.where(Job.status.in_(active_statuses))
        query = query.order_by(Job.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_health(self, job_id: str) -> dict[str, Any]:
        """Quick health snapshot used by dashboards and at-a-glance views."""
        job = await self._get_job(job_id)
        prof = await self.get_profitability(job_id)
        forecast = await self.forecast_completion(job_id)

        flagged = bool(job.notes and "[at-risk" in (job.notes or ""))

        return {
            "job_id": job.id,
            "job_number": job.job_number,
            "status": job.status.value,
            "at_risk": flagged or job.status == JobStatus.ON_HOLD,
            "margin_percent": prof["margin_percent"],
            "on_track": forecast["on_track"],
            "change_order_count": job.change_order_count,
        }

    async def closeout(self, job_id: str) -> Job:
        """Close out a complete job and signal maintenance hand-off."""
        job = await self._get_job(job_id)

        if job.status not in (
            JobStatus.PUNCH_LIST,
            JobStatus.IN_PROGRESS,
        ):
            raise ValueError(
                f"Cannot closeout job {job.job_number} from status {job.status.value}"
            )

        job.status = JobStatus.COMPLETE
        if job.actual_end_date is None:
            job.actual_end_date = date.today()

        stamp = datetime.now(timezone.utc).isoformat()
        handoff = f"[closeout {stamp}] maintenance contract kickoff queued"
        job.notes = f"{job.notes}\n{handoff}" if job.notes else handoff

        await self.db.commit()
        await self.db.refresh(job)
        return job
