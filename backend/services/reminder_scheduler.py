"""
NoblePort Payment Reminder Scheduler

Automated daily cron that chases unpaid milestones and overdue payments.
Stops leaving money on the table.

Runs as part of the app lifespan background loop.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import async_session
from backend.models.job import Job
from backend.models.milestone import Milestone, MilestoneStatus
from backend.models.proposal import Proposal, ProposalStatus
from backend.services.notification_service import NotificationService
from backend.services.stripe_service import StripeService

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """
    Background scheduler that:
    1. Voids expired proposals
    2. Sends reminders for unpaid milestones
    3. Escalates overdue payments
    """

    def __init__(self):
        self.notifications = NotificationService()
        self.stripe = StripeService()
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the daily reminder loop."""
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Reminder scheduler started")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_loop(self):
        """Run reminders every 24 hours."""
        while True:
            try:
                await self.run_all_reminders()
            except Exception as e:
                logger.error(f"Reminder cycle failed: {e}")
            await asyncio.sleep(86400)  # 24 hours

    async def run_all_reminders(self) -> dict:
        """Execute a full reminder cycle. Can be called manually."""
        now = datetime.now(timezone.utc)
        results = {
            "expired_proposals": 0,
            "milestone_reminders_sent": 0,
            "overdue_escalations": 0,
            "timestamp": now.isoformat(),
        }

        # 1. Void expired proposals
        results["expired_proposals"] = await self._void_expired_proposals(now)

        # 2. Remind unpaid milestones
        reminded, escalated = await self._process_unpaid_milestones(now)
        results["milestone_reminders_sent"] = reminded
        results["overdue_escalations"] = escalated

        logger.info(f"Reminder cycle complete: {results}")
        return results

    async def _void_expired_proposals(self, now: datetime) -> int:
        """Void proposals that have passed their expiration date without deposit."""
        count = 0
        async with async_session() as db:
            result = await db.execute(
                select(Proposal).where(
                    Proposal.status.in_([
                        ProposalStatus.SENT,
                        ProposalStatus.SIGNED,
                        ProposalStatus.DEPOSIT_PENDING,
                    ]),
                    Proposal.expires_at.isnot(None),
                    Proposal.expires_at < now,
                )
            )
            for proposal in result.scalars():
                proposal.status = ProposalStatus.VOID
                count += 1
                logger.info(f"Voided expired proposal {proposal.id}: {proposal.title}")

            await db.commit()
        return count

    async def _process_unpaid_milestones(
        self, now: datetime
    ) -> tuple[int, int]:
        """Send reminders for pending milestones, escalate overdue ones."""
        reminded = 0
        escalated = 0

        async with async_session() as db:
            # Find pending and overdue milestones with past due dates
            result = await db.execute(
                select(Milestone).where(
                    Milestone.status.in_([
                        MilestoneStatus.PENDING,
                        MilestoneStatus.REMINDED,
                        MilestoneStatus.OVERDUE,
                    ]),
                    Milestone.due_date.isnot(None),
                    Milestone.due_date < now,
                )
            )

            for milestone in result.scalars():
                # Get the job for client info
                job_result = await db.execute(
                    select(Job).where(Job.id == milestone.job_id)
                )
                job = job_result.scalar_one_or_none()
                if not job:
                    continue

                # Determine severity
                if milestone.status == MilestoneStatus.PENDING:
                    # First reminder
                    milestone.status = MilestoneStatus.REMINDED
                    milestone.reminder_count += 1
                    milestone.last_reminded_at = now

                    await self.notifications.send_payment_reminder(
                        client_email=job.client_email,
                        client_phone=job.client_phone,
                        subject=f"Payment Due: {milestone.title}",
                        message=(
                            f"Hi {job.client_name},\n\n"
                            f"Payment of ${milestone.amount_cents / 100:,.2f} "
                            f"is due for {milestone.title} on {job.title}."
                        ),
                    )
                    reminded += 1

                elif milestone.reminder_count >= 3:
                    # Escalate to overdue
                    milestone.status = MilestoneStatus.OVERDUE
                    milestone.reminder_count += 1
                    milestone.last_reminded_at = now

                    await self.notifications.notify_ops_team(
                        subject=f"OVERDUE: {milestone.title} - {job.client_name}",
                        message=(
                            f"Milestone {milestone.title} is overdue "
                            f"(${milestone.amount_cents / 100:,.2f}) "
                            f"after {milestone.reminder_count} reminders."
                        ),
                        job_data={
                            "job_id": job.id,
                            "client": job.client_name,
                            "email": job.client_email,
                            "phone": job.client_phone,
                            "amount": f"${milestone.amount_cents / 100:,.2f}",
                        },
                    )
                    escalated += 1

                else:
                    # Follow-up reminder
                    milestone.reminder_count += 1
                    milestone.last_reminded_at = now

                    await self.notifications.send_payment_reminder(
                        client_email=job.client_email,
                        client_phone=job.client_phone,
                        subject=f"Reminder: Payment Due for {milestone.title}",
                        message=(
                            f"Hi {job.client_name},\n\n"
                            f"This is a reminder that payment of "
                            f"${milestone.amount_cents / 100:,.2f} "
                            f"is overdue for {milestone.title} on {job.title}.\n\n"
                            f"Please remit payment at your earliest convenience."
                        ),
                    )
                    reminded += 1

            await db.commit()

        return reminded, escalated
