"""
NoblePort Job Pipeline Service

The core revenue-to-production pipeline:
  Deposit paid → Job created → Ops tasks auto-generated → Scheduling triggered

This is the engine that turns payment into field work.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import async_session
from backend.models.job import Job, JobStatus
from backend.models.milestone import Milestone, MilestoneStatus
from backend.models.ops_task import OpsTask, OpsTaskStatus, OpsTaskType
from backend.models.proposal import Proposal, ProposalStatus

logger = logging.getLogger(__name__)


class JobPipeline:
    """
    Orchestrates the full lifecycle:
    proposal deposit → job creation → scheduling → milestones → completion
    """

    async def create_job_from_proposal(self, proposal_id: str) -> dict[str, Any]:
        """
        Create a job when deposit clears. This is the trigger point
        where signature + payment = real commitment.
        """
        async with async_session() as db:
            result = await db.execute(
                select(Proposal).where(Proposal.id == proposal_id)
            )
            proposal = result.scalar_one_or_none()
            if not proposal:
                return {"error": "Proposal not found"}

            if proposal.job_id:
                return {"error": "Job already created for this proposal", "job_id": proposal.job_id}

            # Create the job
            job = Job(
                proposal_id=proposal.id,
                title=proposal.title,
                description=proposal.description,
                scope_of_work=proposal.scope_of_work,
                status=JobStatus.CREATED,
                client_name=proposal.client_name,
                client_email=proposal.client_email,
                client_phone=proposal.client_phone,
                contract_amount_cents=proposal.total_amount_cents,
                deposit_collected_cents=proposal.deposit_amount_cents,
                property_address=proposal.property_address,
                city=proposal.city,
                state=proposal.state,
                zip_code=proposal.zip_code,
            )
            db.add(job)
            await db.flush()

            # Link job back to proposal
            proposal.job_id = job.id
            proposal.status = ProposalStatus.ACTIVE

            # Auto-create default milestones
            remaining = proposal.total_amount_cents - proposal.deposit_amount_cents
            milestones_config = [
                ("Deposit", proposal.deposit_amount_cents, 0, MilestoneStatus.PAID),
                ("50% Completion", remaining // 2, 1, MilestoneStatus.UPCOMING),
                ("Final Payment", remaining - (remaining // 2), 2, MilestoneStatus.UPCOMING),
            ]

            now = datetime.now(timezone.utc)
            for title, amount, seq, status in milestones_config:
                m = Milestone(
                    job_id=job.id,
                    title=title,
                    sequence=seq,
                    amount_cents=amount,
                    status=status,
                    amount_paid_cents=amount if status == MilestoneStatus.PAID else 0,
                    paid_at=now if status == MilestoneStatus.PAID else None,
                )
                db.add(m)

            # Auto-create scheduling tasks
            await self._create_scheduling_tasks(db, job)

            await db.commit()

            logger.info(
                f"Job {job.id} created from proposal {proposal.id} "
                f"(${job.contract_amount_cents / 100:.2f})"
            )

            return {
                "job_id": job.id,
                "proposal_id": proposal.id,
                "title": job.title,
                "contract_amount": job.contract_amount_cents / 100,
                "deposit_collected": job.deposit_collected_cents / 100,
                "status": job.status.value,
                "ops_tasks_created": True,
            }

    async def _create_scheduling_tasks(self, db: AsyncSession, job: Job):
        """
        Auto-generate ops tasks when a job is created.
        This is what pushes revenue into field production.
        """
        now = datetime.now(timezone.utc)

        tasks = [
            OpsTask(
                job_id=job.id,
                task_type=OpsTaskType.SCHEDULE_SITE_VISIT,
                status=OpsTaskStatus.OPEN,
                title=f"Schedule site visit for {job.title}",
                description=f"Client: {job.client_name}, Address: {job.property_address}",
                due_at=now + timedelta(days=2),
            ),
            OpsTask(
                job_id=job.id,
                task_type=OpsTaskType.ASSIGN_CREW,
                status=OpsTaskStatus.OPEN,
                title=f"Assign crew for {job.title}",
                description=f"Contract: ${job.contract_amount_cents / 100:,.2f}",
                due_at=now + timedelta(days=3),
            ),
            OpsTask(
                job_id=job.id,
                task_type=OpsTaskType.ORDER_MATERIALS,
                status=OpsTaskStatus.OPEN,
                title=f"Review materials needed for {job.title}",
                due_at=now + timedelta(days=4),
            ),
            OpsTask(
                job_id=job.id,
                task_type=OpsTaskType.CONFIRM_START_DATE,
                status=OpsTaskStatus.OPEN,
                title=f"Confirm start date with client for {job.title}",
                description=f"Contact {job.client_name} at {job.client_email}",
                due_at=now + timedelta(days=5),
            ),
        ]

        for task in tasks:
            db.add(task)

        logger.info(f"Created {len(tasks)} ops tasks for job {job.id}")

    async def handle_deposit_payment(
        self,
        proposal_id: str,
        payment_intent_id: str,
    ) -> dict[str, Any]:
        """
        Called by Stripe webhook when deposit payment succeeds.
        Triggers the full job creation pipeline.
        """
        async with async_session() as db:
            result = await db.execute(
                select(Proposal).where(Proposal.id == proposal_id)
            )
            proposal = result.scalar_one_or_none()
            if not proposal:
                return {"error": "Proposal not found"}

            proposal.status = ProposalStatus.DEPOSIT_PAID
            proposal.stripe_payment_intent_id = payment_intent_id
            proposal.deposit_paid_at = datetime.now(timezone.utc)
            await db.commit()

        # Now create the job
        return await self.create_job_from_proposal(proposal_id)

    async def handle_milestone_payment(
        self,
        milestone_id: str,
        payment_intent_id: str,
    ) -> dict[str, Any]:
        """Called by Stripe webhook when a milestone payment succeeds."""
        async with async_session() as db:
            result = await db.execute(
                select(Milestone).where(Milestone.id == milestone_id)
            )
            milestone = result.scalar_one_or_none()
            if not milestone:
                return {"error": "Milestone not found"}

            now = datetime.now(timezone.utc)
            milestone.status = MilestoneStatus.PAID
            milestone.amount_paid_cents = milestone.amount_cents
            milestone.paid_at = now
            milestone.stripe_payment_intent_id = payment_intent_id

            # Update job totals
            job_result = await db.execute(
                select(Job).where(Job.id == milestone.job_id)
            )
            job = job_result.scalar_one_or_none()
            if job:
                job.total_paid_cents += milestone.amount_cents

            await db.commit()

            logger.info(
                f"Milestone {milestone.id} paid: ${milestone.amount_cents / 100:.2f}"
            )

            return {
                "milestone_id": milestone.id,
                "job_id": milestone.job_id,
                "amount_paid": milestone.amount_cents / 100,
                "status": milestone.status.value,
            }

    async def handle_change_order_payment(
        self,
        change_order_id: str,
        payment_intent_id: str,
    ) -> dict[str, Any]:
        """Called by Stripe webhook when a change order payment succeeds."""
        from backend.models.change_order import ChangeOrder, ChangeOrderStatus

        async with async_session() as db:
            result = await db.execute(
                select(ChangeOrder).where(ChangeOrder.id == change_order_id)
            )
            co = result.scalar_one_or_none()
            if not co:
                return {"error": "Change order not found"}

            now = datetime.now(timezone.utc)
            co.status = ChangeOrderStatus.PAID
            co.paid_at = now
            co.stripe_payment_intent_id = payment_intent_id

            # Update job totals
            job_result = await db.execute(
                select(Job).where(Job.id == co.job_id)
            )
            job = job_result.scalar_one_or_none()
            if job:
                job.change_order_total_cents += co.amount_cents
                job.total_paid_cents += co.amount_cents

            await db.commit()

            logger.info(
                f"Change order {co.id} paid: ${co.amount_cents / 100:.2f}"
            )

            return {
                "change_order_id": co.id,
                "job_id": co.job_id,
                "amount_paid": co.amount_cents / 100,
                "status": co.status.value,
            }
