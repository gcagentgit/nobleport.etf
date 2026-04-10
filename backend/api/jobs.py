"""
NoblePort Jobs API

Job management, milestone tracking, and ops task oversight.
Jobs are the operational entity that drives field production.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.models.job import Job, JobStatus
from backend.models.milestone import Milestone, MilestoneStatus
from backend.models.ops_task import OpsTask, OpsTaskStatus
from backend.services.stripe_service import StripeService

router = APIRouter()
stripe_service = StripeService()


class JobResponse(BaseModel):
    id: str
    proposal_id: str
    project_id: str | None
    title: str
    description: str | None
    status: str
    client_name: str
    client_email: str
    client_phone: str | None
    contract_amount_cents: int
    deposit_collected_cents: int
    total_invoiced_cents: int
    total_paid_cents: int
    change_order_total_cents: int
    property_address: str | None
    city: str | None
    state: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    assigned_crew: str | None
    project_manager: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MilestoneResponse(BaseModel):
    id: str
    job_id: str
    title: str
    description: str | None
    sequence: int
    status: str
    amount_cents: int
    amount_paid_cents: int
    due_date: datetime | None
    paid_at: datetime | None
    reminder_count: int
    stripe_checkout_session_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OpsTaskResponse(BaseModel):
    id: str
    job_id: str
    task_type: str
    status: str
    title: str
    description: str | None
    assigned_to: str | None
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobStatusUpdate(BaseModel):
    status: str
    assigned_crew: str | None = None
    project_manager: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None


class OpsTaskUpdate(BaseModel):
    status: str | None = None
    assigned_to: str | None = None


# --- Job Endpoints ---

@router.get("")
async def list_jobs(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Job)
    if status:
        query = query.where(Job.status == JobStatus(status))
    query = query.order_by(Job.created_at.desc())
    result = await db.execute(query)
    return [JobResponse.model_validate(j) for j in result.scalars()]


@router.get("/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@router.patch("/{job_id}")
async def update_job(job_id: str, data: JobStatusUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus(data.status)
    if data.assigned_crew is not None:
        job.assigned_crew = data.assigned_crew
    if data.project_manager is not None:
        job.project_manager = data.project_manager
    if data.scheduled_start is not None:
        job.scheduled_start = data.scheduled_start
    if data.scheduled_end is not None:
        job.scheduled_end = data.scheduled_end

    if data.status == JobStatus.IN_PROGRESS.value and not job.actual_start:
        job.actual_start = datetime.now(timezone.utc)
    if data.status == JobStatus.COMPLETED.value and not job.actual_end:
        job.actual_end = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(job)
    return JobResponse.model_validate(job)


# --- Milestone Endpoints ---

@router.get("/{job_id}/milestones")
async def list_milestones(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Milestone)
        .where(Milestone.job_id == job_id)
        .order_by(Milestone.sequence)
    )
    return [MilestoneResponse.model_validate(m) for m in result.scalars()]


@router.post("/{job_id}/milestones/{milestone_id}/send-payment-link")
async def send_milestone_payment_link(
    job_id: str, milestone_id: str, db: AsyncSession = Depends(get_db)
):
    """Create a Stripe checkout for a milestone and return the payment URL."""
    result = await db.execute(
        select(Milestone).where(Milestone.id == milestone_id, Milestone.job_id == job_id)
    )
    milestone = result.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    if milestone.status == MilestoneStatus.PAID:
        raise HTTPException(status_code=400, detail="Milestone already paid")

    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one()

    # Mark as pending payment
    milestone.status = MilestoneStatus.PENDING
    await db.commit()

    checkout = await stripe_service.create_milestone_checkout(
        milestone=milestone,
        job_title=job.title,
        client_email=job.client_email,
    )
    return checkout


# --- Ops Tasks Endpoints ---

@router.get("/{job_id}/tasks")
async def list_ops_tasks(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OpsTask)
        .where(OpsTask.job_id == job_id)
        .order_by(OpsTask.due_at.asc().nullslast())
    )
    return [OpsTaskResponse.model_validate(t) for t in result.scalars()]


@router.patch("/{job_id}/tasks/{task_id}")
async def update_ops_task(
    job_id: str, task_id: str, data: OpsTaskUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(OpsTask).where(OpsTask.id == task_id, OpsTask.job_id == job_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if data.status:
        task.status = OpsTaskStatus(data.status)
        if data.status == OpsTaskStatus.COMPLETED.value:
            task.completed_at = datetime.now(timezone.utc)
    if data.assigned_to is not None:
        task.assigned_to = data.assigned_to

    await db.commit()
    await db.refresh(task)
    return OpsTaskResponse.model_validate(task)
