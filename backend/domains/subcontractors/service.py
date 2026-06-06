"""
NoblePort Subcontractors Service

Sub directory, bids, assignments, insurance compliance, and payments.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.subcontractors.models import (
    AssignmentStatus,
    BidStatus,
    Subcontractor,
    SubcontractorAssignment,
    SubcontractorBid,
    SubcontractorPayment,
)


class SubcontractorsService:
    """Service for managing the subcontractor directory and lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_sub(self, sub_id: str) -> Subcontractor:
        result = await self.db.execute(
            select(Subcontractor).where(Subcontractor.id == sub_id)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            raise ValueError(f"Subcontractor {sub_id} not found")
        return sub

    async def _get_bid(self, bid_id: str) -> SubcontractorBid:
        result = await self.db.execute(
            select(SubcontractorBid).where(SubcontractorBid.id == bid_id)
        )
        bid = result.scalar_one_or_none()
        if not bid:
            raise ValueError(f"Bid {bid_id} not found")
        return bid

    async def _get_assignment(self, assignment_id: str) -> SubcontractorAssignment:
        result = await self.db.execute(
            select(SubcontractorAssignment).where(
                SubcontractorAssignment.id == assignment_id
            )
        )
        a = result.scalar_one_or_none()
        if not a:
            raise ValueError(f"Assignment {assignment_id} not found")
        return a

    async def add_subcontractor(self, **fields: Any) -> Subcontractor:
        if "business_name" not in fields or "trade" not in fields:
            raise ValueError("business_name and trade are required")
        sub = Subcontractor(**fields)
        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def update_subcontractor(self, sub_id: str, **fields: Any) -> Subcontractor:
        sub = await self._get_sub(sub_id)
        for k, v in fields.items():
            if v is not None and hasattr(sub, k):
                setattr(sub, k, v)
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def update_insurance(
        self,
        sub_id: str,
        carrier: str,
        policy: str,
        expires: date,
    ) -> Subcontractor:
        sub = await self._get_sub(sub_id)
        sub.insurance_carrier = carrier
        sub.insurance_policy_number = policy
        sub.insurance_expires = expires
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def get_expiring_insurance(self, within_days: int = 30) -> list[Subcontractor]:
        horizon = date.today() + timedelta(days=within_days)
        result = await self.db.execute(
            select(Subcontractor)
            .where(
                Subcontractor.insurance_expires.is_not(None),
                Subcontractor.insurance_expires <= horizon,
            )
            .order_by(Subcontractor.insurance_expires.asc())
        )
        return list(result.scalars().all())

    async def flag_insurance_lapsed(self, sub_id: str) -> Subcontractor:
        """Mark a sub as non-preferred when their coverage has lapsed."""
        sub = await self._get_sub(sub_id)
        sub.preferred = False
        stamp = datetime.now(timezone.utc).isoformat()
        line = f"[insurance-lapsed {stamp}]"
        sub.notes = f"{sub.notes}\n{line}" if sub.notes else line
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def get_subcontractor(self, sub_id: str) -> Subcontractor:
        return await self._get_sub(sub_id)

    async def list_subcontractors(
        self,
        trade: str | None = None,
        preferred: bool | None = None,
    ) -> list[Subcontractor]:
        query = select(Subcontractor)
        if trade:
            query = query.where(Subcontractor.trade == trade)
        if preferred is not None:
            query = query.where(Subcontractor.preferred == preferred)
        query = query.order_by(Subcontractor.business_name.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_preferred_subs_for_trade(self, trade: str) -> list[Subcontractor]:
        result = await self.db.execute(
            select(Subcontractor)
            .where(
                Subcontractor.trade == trade,
                Subcontractor.preferred.is_(True),
            )
            .order_by(Subcontractor.rating.desc().nullslast())
        )
        return list(result.scalars().all())

    async def record_bid(
        self,
        sub_id: str,
        job_id: str,
        trade: str,
        bid_amount: float,
        scope_summary: str | None = None,
        valid_until: date | None = None,
    ) -> SubcontractorBid:
        await self._get_sub(sub_id)  # validate exists
        bid = SubcontractorBid(
            subcontractor_id=sub_id,
            job_id=job_id,
            trade=trade,
            bid_amount=bid_amount,
            scope_summary=scope_summary,
            valid_until=valid_until,
            status=BidStatus.PENDING,
            submitted_at=datetime.now(timezone.utc),
        )
        self.db.add(bid)
        await self.db.commit()
        await self.db.refresh(bid)
        return bid

    async def award_bid(
        self, bid_id: str, decided_by: str | None = None
    ) -> SubcontractorBid:
        """Accept the bid and reject any competing pending bids on the same job/trade."""
        bid = await self._get_bid(bid_id)
        now = datetime.now(timezone.utc)

        # Reject competitors first
        competitors_result = await self.db.execute(
            select(SubcontractorBid).where(
                SubcontractorBid.job_id == bid.job_id,
                SubcontractorBid.trade == bid.trade,
                SubcontractorBid.id != bid.id,
                SubcontractorBid.status == BidStatus.PENDING,
            )
        )
        for competitor in competitors_result.scalars().all():
            competitor.status = BidStatus.REJECTED
            competitor.decided_at = now
            competitor.decided_by = decided_by

        bid.status = BidStatus.ACCEPTED
        bid.decided_at = now
        bid.decided_by = decided_by

        await self.db.commit()
        await self.db.refresh(bid)
        return bid

    async def assign_to_job(
        self,
        sub_id: str,
        job_id: str,
        scope: str | None,
        contract_amount: float,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> SubcontractorAssignment:
        await self._get_sub(sub_id)  # validate
        assignment = SubcontractorAssignment(
            subcontractor_id=sub_id,
            job_id=job_id,
            scope=scope,
            contract_amount=contract_amount,
            start_date=start_date,
            end_date=end_date,
            status=AssignmentStatus.SCHEDULED,
        )
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment

    async def list_assignments(
        self,
        job_id: str | None = None,
        sub_id: str | None = None,
        status: AssignmentStatus | None = None,
    ) -> list[SubcontractorAssignment]:
        query = select(SubcontractorAssignment)
        if job_id:
            query = query.where(SubcontractorAssignment.job_id == job_id)
        if sub_id:
            query = query.where(SubcontractorAssignment.subcontractor_id == sub_id)
        if status is not None:
            query = query.where(SubcontractorAssignment.status == status)
        query = query.order_by(SubcontractorAssignment.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_bids(
        self,
        job_id: str | None = None,
        sub_id: str | None = None,
        status: BidStatus | None = None,
    ) -> list[SubcontractorBid]:
        query = select(SubcontractorBid)
        if job_id:
            query = query.where(SubcontractorBid.job_id == job_id)
        if sub_id:
            query = query.where(SubcontractorBid.subcontractor_id == sub_id)
        if status is not None:
            query = query.where(SubcontractorBid.status == status)
        query = query.order_by(SubcontractorBid.submitted_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def record_payment(
        self,
        assignment_id: str,
        amount: float,
        payment_method: str | None = None,
        reference_number: str | None = None,
        lien_waiver_received: bool = False,
        paid_at: datetime | None = None,
    ) -> SubcontractorPayment:
        assignment = await self._get_assignment(assignment_id)
        payment = SubcontractorPayment(
            subcontractor_id=assignment.subcontractor_id,
            assignment_id=assignment.id,
            amount=amount,
            paid_at=paid_at or datetime.now(timezone.utc),
            payment_method=payment_method,
            reference_number=reference_number,
            lien_waiver_received=lien_waiver_received,
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def list_payments_for_sub(self, sub_id: str) -> list[SubcontractorPayment]:
        result = await self.db.execute(
            select(SubcontractorPayment)
            .where(SubcontractorPayment.subcontractor_id == sub_id)
            .order_by(SubcontractorPayment.paid_at.desc())
        )
        return list(result.scalars().all())

    # ----- Serializers -----

    @staticmethod
    def sub_to_dict(sub: Subcontractor) -> dict[str, Any]:
        return {
            "id": sub.id,
            "business_name": sub.business_name,
            "contact_name": sub.contact_name,
            "trade": sub.trade,
            "additional_trades": sub.additional_trades,
            "email": sub.email,
            "phone": sub.phone,
            "license_number": sub.license_number,
            "license_expires": sub.license_expires,
            "insurance_carrier": sub.insurance_carrier,
            "insurance_policy_number": sub.insurance_policy_number,
            "insurance_expires": sub.insurance_expires,
            "w9_on_file": sub.w9_on_file,
            "preferred": sub.preferred,
            "rating": sub.rating,
        }

    @staticmethod
    def bid_to_dict(bid: SubcontractorBid) -> dict[str, Any]:
        return {
            "id": bid.id,
            "subcontractor_id": bid.subcontractor_id,
            "job_id": bid.job_id,
            "trade": bid.trade,
            "bid_amount": bid.bid_amount,
            "scope_summary": bid.scope_summary,
            "valid_until": bid.valid_until,
            "status": bid.status.value,
            "submitted_at": bid.submitted_at,
            "decided_at": bid.decided_at,
            "decided_by": bid.decided_by,
        }

    @staticmethod
    def assignment_to_dict(a: SubcontractorAssignment) -> dict[str, Any]:
        return {
            "id": a.id,
            "subcontractor_id": a.subcontractor_id,
            "job_id": a.job_id,
            "scope": a.scope,
            "contract_amount": a.contract_amount,
            "start_date": a.start_date,
            "end_date": a.end_date,
            "status": a.status.value,
            "performance_notes": a.performance_notes,
        }

    @staticmethod
    def payment_to_dict(p: SubcontractorPayment) -> dict[str, Any]:
        return {
            "id": p.id,
            "subcontractor_id": p.subcontractor_id,
            "assignment_id": p.assignment_id,
            "amount": p.amount,
            "paid_at": p.paid_at,
            "payment_method": p.payment_method,
            "reference_number": p.reference_number,
            "lien_waiver_received": p.lien_waiver_received,
        }
