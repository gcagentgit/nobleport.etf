"""
NoblePort Construction Service

Field-operations business logic: daily logs, crew status, materials,
safety incidents, and cross-site rollups.
"""

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.daily_log import DailyLog, WeatherCondition
from backend.models.job import Job, JobStatus
from backend.models.schedule import ScheduleItem, TaskStatus


class ConstructionService:
    """Service for daily field operations across all active sites."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_job(self, job_id: str) -> Job:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        return job

    async def submit_daily_log(
        self,
        job_id: str,
        log_data: dict[str, Any],
    ) -> DailyLog:
        """Create a structured daily log for a job's underlying project."""
        job = await self._get_job(job_id)
        if not job.project_id:
            raise ValueError(
                f"Job {job.job_number} has no linked project; cannot log activity"
            )

        log_date_value = log_data.get("log_date") or date.today()
        weather_value = log_data.get("weather")
        if isinstance(weather_value, str):
            weather_value = WeatherCondition(weather_value)

        log = DailyLog(
            project_id=job.project_id,
            log_date=log_date_value,
            author=log_data.get("author", "system"),
            weather=weather_value,
            temperature_high_f=log_data.get("temperature_high_f"),
            temperature_low_f=log_data.get("temperature_low_f"),
            weather_delay_hours=log_data.get("weather_delay_hours", 0.0),
            crew_count=log_data.get("crew_count", 0),
            subcontractors_on_site=log_data.get("subcontractors_on_site"),
            total_man_hours=log_data.get("total_man_hours", 0.0),
            work_performed=log_data.get("work_performed"),
            materials_received=log_data.get("materials_received"),
            equipment_used=log_data.get("equipment_used"),
            safety_incidents=log_data.get("safety_incidents"),
            safety_meeting_held=log_data.get("safety_meeting_held"),
            osha_notes=log_data.get("osha_notes"),
            visitors=log_data.get("visitors"),
            inspections_conducted=log_data.get("inspections_conducted"),
            notes=log_data.get("notes"),
            issues=log_data.get("issues"),
            delays=log_data.get("delays"),
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_field_status(self, job_id: str) -> dict[str, Any]:
        """Return live field status for a job: crew, weather, last log, in-progress tasks."""
        job = await self._get_job(job_id)

        last_log = None
        if job.project_id:
            log_result = await self.db.execute(
                select(DailyLog)
                .where(DailyLog.project_id == job.project_id)
                .order_by(DailyLog.log_date.desc())
                .limit(1)
            )
            last_log = log_result.scalar_one_or_none()

        in_progress: list[ScheduleItem] = []
        if job.project_id:
            task_result = await self.db.execute(
                select(ScheduleItem).where(
                    ScheduleItem.project_id == job.project_id,
                    ScheduleItem.status == TaskStatus.IN_PROGRESS,
                )
            )
            in_progress = list(task_result.scalars().all())

        return {
            "job_id": job.id,
            "job_number": job.job_number,
            "job_status": job.status.value,
            "site_address": job.site_address,
            "crew": job.crew,
            "last_log": {
                "log_date": last_log.log_date if last_log else None,
                "author": last_log.author if last_log else None,
                "crew_count": last_log.crew_count if last_log else None,
                "weather": last_log.weather.value
                if last_log and last_log.weather
                else None,
                "work_performed": last_log.work_performed if last_log else None,
            }
            if last_log
            else None,
            "in_progress_tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "trade": t.trade,
                    "assigned_to": t.assigned_to,
                    "percent_complete": t.percent_complete,
                }
                for t in in_progress
            ],
        }

    async def record_material_delivery(
        self, job_id: str, materials: str, received_by: str | None = None
    ) -> DailyLog:
        """Append a material-delivery line item via a daily log entry."""
        job = await self._get_job(job_id)
        if not job.project_id:
            raise ValueError(
                f"Job {job.job_number} has no linked project for material tracking"
            )

        log = DailyLog(
            project_id=job.project_id,
            log_date=date.today(),
            author=received_by or "delivery-system",
            materials_received=materials,
            notes=f"[material-delivery] {materials}",
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def report_safety_incident(
        self,
        job_id: str,
        details: str,
        reported_by: str | None = None,
        critical: bool = False,
    ) -> DailyLog:
        """Capture a safety incident. Critical incidents put the job on hold."""
        job = await self._get_job(job_id)
        if not job.project_id:
            raise ValueError(
                f"Job {job.job_number} has no linked project for safety logging"
            )

        log = DailyLog(
            project_id=job.project_id,
            log_date=date.today(),
            author=reported_by or "safety-officer",
            safety_incidents=details,
            notes=f"[safety-incident{' CRITICAL' if critical else ''}] {details}",
        )
        self.db.add(log)

        if critical and job.status == JobStatus.IN_PROGRESS:
            job.status = JobStatus.ON_HOLD
            stamp = datetime.now(timezone.utc).isoformat()
            flag = f"[safety-hold {stamp}] {details}"
            job.notes = f"{job.notes}\n{flag}" if job.notes else flag

        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_today_active_sites(self) -> list[dict[str, Any]]:
        """Roll up all active sites with a daily log for today."""
        today = date.today()
        active_result = await self.db.execute(
            select(Job).where(
                Job.status.in_(
                    [
                        JobStatus.IN_PROGRESS,
                        JobStatus.PUNCH_LIST,
                        JobStatus.SCHEDULED,
                    ]
                )
            )
        )
        active_jobs = list(active_result.scalars().all())

        sites: list[dict[str, Any]] = []
        for job in active_jobs:
            has_log_today = False
            if job.project_id:
                log_result = await self.db.execute(
                    select(DailyLog).where(
                        DailyLog.project_id == job.project_id,
                        DailyLog.log_date == today,
                    )
                )
                has_log_today = log_result.scalar_one_or_none() is not None

            sites.append(
                {
                    "job_id": job.id,
                    "job_number": job.job_number,
                    "status": job.status.value,
                    "crew": job.crew,
                    "site_address": job.site_address,
                    "site_city": job.site_city,
                    "logged_today": has_log_today,
                }
            )
        return sites

    async def get_crew_locations(self) -> list[dict[str, Any]]:
        """Return which crew is at which job/site right now."""
        result = await self.db.execute(
            select(Job).where(
                Job.status.in_([JobStatus.IN_PROGRESS, JobStatus.PUNCH_LIST]),
                Job.crew.is_not(None),
            )
        )
        jobs = list(result.scalars().all())
        return [
            {
                "job_id": j.id,
                "job_number": j.job_number,
                "crew": j.crew,
                "site_address": j.site_address,
                "site_city": j.site_city,
                "site_state": j.site_state,
            }
            for j in jobs
        ]
