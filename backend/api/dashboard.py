"""
NoblePort Ops Dashboard API

Real-time pipeline view for operations management.
Shows active jobs, collected deposits, unpaid milestones,
jobs stuck in scheduling, and revenue pipeline metrics.

This is the single pane of glass for the business.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.models.change_order import ChangeOrder, ChangeOrderStatus
from backend.models.job import Job, JobStatus
from backend.models.milestone import Milestone, MilestoneStatus
from backend.models.ops_task import OpsTask, OpsTaskStatus
from backend.models.proposal import Proposal, ProposalStatus

router = APIRouter()


@router.get("/summary")
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Full operational dashboard in a single call."""
    now = datetime.now(timezone.utc)

    # --- Proposal Pipeline ---
    proposals_by_status = {}
    for status in ProposalStatus:
        result = await db.execute(
            select(func.count()).select_from(Proposal).where(Proposal.status == status)
        )
        count = result.scalar()
        if count > 0:
            proposals_by_status[status.value] = count

    total_proposal_value = await db.execute(
        select(func.coalesce(func.sum(Proposal.total_amount_cents), 0))
        .select_from(Proposal)
        .where(Proposal.status.in_([
            ProposalStatus.SENT,
            ProposalStatus.SIGNED,
            ProposalStatus.DEPOSIT_PENDING,
        ]))
    )

    # --- Job Pipeline ---
    jobs_by_status = {}
    for status in JobStatus:
        result = await db.execute(
            select(func.count()).select_from(Job).where(Job.status == status)
        )
        count = result.scalar()
        if count > 0:
            jobs_by_status[status.value] = count

    active_job_statuses = [
        JobStatus.CREATED, JobStatus.SCHEDULING, JobStatus.SCHEDULED,
        JobStatus.IN_PROGRESS, JobStatus.INSPECTION, JobStatus.PUNCH_LIST,
    ]

    total_contract_value = await db.execute(
        select(func.coalesce(func.sum(Job.contract_amount_cents), 0))
        .select_from(Job)
        .where(Job.status.in_(active_job_statuses))
    )
    total_deposits = await db.execute(
        select(func.coalesce(func.sum(Job.deposit_collected_cents), 0))
        .select_from(Job)
    )
    total_paid = await db.execute(
        select(func.coalesce(func.sum(Job.total_paid_cents), 0))
        .select_from(Job)
    )
    total_change_orders = await db.execute(
        select(func.coalesce(func.sum(Job.change_order_total_cents), 0))
        .select_from(Job)
    )

    # --- Milestones ---
    unpaid_milestones = await db.execute(
        select(func.count())
        .select_from(Milestone)
        .where(Milestone.status.in_([
            MilestoneStatus.PENDING, MilestoneStatus.REMINDED, MilestoneStatus.OVERDUE,
        ]))
    )
    unpaid_milestone_value = await db.execute(
        select(func.coalesce(func.sum(Milestone.amount_cents), 0))
        .select_from(Milestone)
        .where(Milestone.status.in_([
            MilestoneStatus.PENDING, MilestoneStatus.REMINDED, MilestoneStatus.OVERDUE,
        ]))
    )
    overdue_count = await db.execute(
        select(func.count())
        .select_from(Milestone)
        .where(Milestone.status == MilestoneStatus.OVERDUE)
    )

    # --- Ops Tasks ---
    open_tasks = await db.execute(
        select(func.count())
        .select_from(OpsTask)
        .where(OpsTask.status == OpsTaskStatus.OPEN)
    )
    overdue_tasks = await db.execute(
        select(func.count())
        .select_from(OpsTask)
        .where(OpsTask.status == OpsTaskStatus.OPEN, OpsTask.due_at < now)
    )

    # --- Change Orders ---
    pending_cos = await db.execute(
        select(func.count())
        .select_from(ChangeOrder)
        .where(ChangeOrder.status == ChangeOrderStatus.PENDING_APPROVAL)
    )
    pending_co_value = await db.execute(
        select(func.coalesce(func.sum(ChangeOrder.amount_cents), 0))
        .select_from(ChangeOrder)
        .where(ChangeOrder.status == ChangeOrderStatus.PENDING_APPROVAL)
    )

    return {
        "generated_at": now.isoformat(),
        "proposals": {
            "by_status": proposals_by_status,
            "pending_value_cents": total_proposal_value.scalar(),
        },
        "jobs": {
            "by_status": jobs_by_status,
            "active_contract_value_cents": total_contract_value.scalar(),
            "total_deposits_collected_cents": total_deposits.scalar(),
            "total_revenue_collected_cents": total_paid.scalar(),
            "change_order_revenue_cents": total_change_orders.scalar(),
        },
        "milestones": {
            "unpaid_count": unpaid_milestones.scalar(),
            "unpaid_value_cents": unpaid_milestone_value.scalar(),
            "overdue_count": overdue_count.scalar(),
        },
        "ops_tasks": {
            "open_count": open_tasks.scalar(),
            "overdue_count": overdue_tasks.scalar(),
        },
        "change_orders": {
            "pending_approval_count": pending_cos.scalar(),
            "pending_value_cents": pending_co_value.scalar(),
        },
    }


@router.get("/jobs")
async def dashboard_jobs(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Active jobs with key metrics: deposit, unpaid milestones, scheduling status.
    The real-time view your ops team needs.
    """
    query = select(Job)
    if status:
        query = query.where(Job.status == JobStatus(status))
    else:
        # Default: show active jobs
        query = query.where(Job.status.in_([
            JobStatus.CREATED, JobStatus.SCHEDULING, JobStatus.SCHEDULED,
            JobStatus.IN_PROGRESS, JobStatus.INSPECTION, JobStatus.PUNCH_LIST,
        ]))
    query = query.order_by(Job.created_at.desc())

    result = await db.execute(query)
    jobs = result.scalars().all()

    job_list = []
    for job in jobs:
        # Get milestone summary
        milestones = await db.execute(
            select(Milestone).where(Milestone.job_id == job.id)
        )
        milestone_list = milestones.scalars().all()
        unpaid = [m for m in milestone_list if m.status != MilestoneStatus.PAID]

        # Get open ops tasks
        tasks = await db.execute(
            select(func.count())
            .select_from(OpsTask)
            .where(OpsTask.job_id == job.id, OpsTask.status == OpsTaskStatus.OPEN)
        )

        # Get pending change orders
        cos = await db.execute(
            select(func.count())
            .select_from(ChangeOrder)
            .where(
                ChangeOrder.job_id == job.id,
                ChangeOrder.status == ChangeOrderStatus.PENDING_APPROVAL,
            )
        )

        job_list.append({
            "id": job.id,
            "title": job.title,
            "status": job.status.value,
            "client_name": job.client_name,
            "property_address": job.property_address,
            "contract_amount": job.contract_amount_cents / 100,
            "deposit_collected": job.deposit_collected_cents / 100,
            "total_paid": job.total_paid_cents / 100,
            "change_orders_total": job.change_order_total_cents / 100,
            "balance_remaining": (
                (job.contract_amount_cents + job.change_order_total_cents - job.total_paid_cents) / 100
            ),
            "unpaid_milestones": len(unpaid),
            "unpaid_milestone_value": sum(m.amount_cents for m in unpaid) / 100,
            "open_ops_tasks": tasks.scalar(),
            "pending_change_orders": cos.scalar(),
            "scheduled_start": job.scheduled_start.isoformat() if job.scheduled_start else None,
            "assigned_crew": job.assigned_crew,
            "created_at": job.created_at.isoformat(),
        })

    return {"jobs": job_list, "count": len(job_list)}


@router.get("/stuck-in-scheduling")
async def stuck_in_scheduling(db: AsyncSession = Depends(get_db)):
    """
    Jobs that are stuck — created or scheduling status with no scheduled start date.
    These are revenue bottlenecks.
    """
    result = await db.execute(
        select(Job).where(
            Job.status.in_([JobStatus.CREATED, JobStatus.SCHEDULING]),
            Job.scheduled_start.is_(None),
        )
    )
    jobs = result.scalars().all()

    return {
        "stuck_jobs": [
            {
                "id": j.id,
                "title": j.title,
                "client_name": j.client_name,
                "contract_amount": j.contract_amount_cents / 100,
                "created_at": j.created_at.isoformat(),
                "days_since_created": (
                    datetime.now(timezone.utc) - j.created_at
                ).days,
            }
            for j in jobs
        ],
        "count": len(jobs),
    }
