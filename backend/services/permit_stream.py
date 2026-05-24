"""
PermitStream Engine — Permit Intelligence MVP

Residential permit workflow engine for Massachusetts North Shore.
Handles deficiency scoring, zoning risk assessment, permit checklist
generation, intake extraction, and submission validation.

Scope locked: residential additions, remodels, decks, new construction <3500 sf.
Municipal priority: Newburyport, Gloucester, Rowley.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.permit import Permit, PermitStatus, PermitType

logger = logging.getLogger(__name__)

MUNICIPAL_RULES: dict[str, dict[str, Any]] = {
    "Newburyport": {
        "median_review_days": 28,
        "p90_review_days": 52,
        "historic_district": True,
        "conservation_overlay": True,
        "requires_zba_variance": ["setback", "lot_coverage", "height"],
        "typical_fees": {"building": 350, "electrical": 100, "plumbing": 100},
    },
    "Gloucester": {
        "median_review_days": 21,
        "p90_review_days": 42,
        "historic_district": True,
        "conservation_overlay": True,
        "requires_zba_variance": ["setback", "lot_coverage"],
        "typical_fees": {"building": 300, "electrical": 75, "plumbing": 75},
    },
    "Rowley": {
        "median_review_days": 18,
        "p90_review_days": 35,
        "historic_district": False,
        "conservation_overlay": False,
        "requires_zba_variance": ["setback"],
        "typical_fees": {"building": 250, "electrical": 50, "plumbing": 50},
    },
    "Ipswich": {
        "median_review_days": 24,
        "p90_review_days": 45,
        "historic_district": True,
        "conservation_overlay": True,
        "requires_zba_variance": ["setback", "height"],
        "typical_fees": {"building": 325, "electrical": 85, "plumbing": 85},
    },
    "Essex": {
        "median_review_days": 16,
        "p90_review_days": 30,
        "historic_district": False,
        "conservation_overlay": True,
        "requires_zba_variance": ["setback"],
        "typical_fees": {"building": 200, "electrical": 50, "plumbing": 50},
    },
    "Manchester-by-the-Sea": {
        "median_review_days": 22,
        "p90_review_days": 40,
        "historic_district": True,
        "conservation_overlay": True,
        "requires_zba_variance": ["setback", "lot_coverage", "height"],
        "typical_fees": {"building": 375, "electrical": 100, "plumbing": 100},
    },
    "Marblehead": {
        "median_review_days": 26,
        "p90_review_days": 48,
        "historic_district": True,
        "conservation_overlay": False,
        "requires_zba_variance": ["setback", "height", "lot_coverage"],
        "typical_fees": {"building": 350, "electrical": 90, "plumbing": 90},
    },
}

RESIDENTIAL_CHECKLIST = [
    {"item": "Plot plan / site survey", "required": True, "category": "site"},
    {"item": "Architectural drawings (stamped)", "required": True, "category": "drawings"},
    {"item": "Structural calculations", "required": True, "category": "engineering"},
    {"item": "Energy code compliance (MA Stretch Code)", "required": True, "category": "energy"},
    {"item": "Title V septic report (if applicable)", "required": False, "category": "site"},
    {"item": "Conservation Commission approval", "required": False, "category": "zoning"},
    {"item": "Historic District Commission approval", "required": False, "category": "zoning"},
    {"item": "ZBA variance (if required)", "required": False, "category": "zoning"},
    {"item": "Contractor license verification", "required": True, "category": "compliance"},
    {"item": "Workers comp certificate", "required": True, "category": "compliance"},
    {"item": "General liability insurance", "required": True, "category": "compliance"},
    {"item": "Owner authorization letter", "required": True, "category": "admin"},
    {"item": "Application form (signed)", "required": True, "category": "admin"},
    {"item": "Fee payment", "required": True, "category": "admin"},
]


class PermitStreamEngine:

    @staticmethod
    async def create_permit(
        db: AsyncSession,
        ahj: str,
        property_address: str,
        permit_type: PermitType,
        *,
        job_id: str | None = None,
        lead_id: str | None = None,
        project_description: str | None = None,
        scope_type: str | None = None,
        estimated_cost: float = 0.0,
        square_footage: float | None = None,
    ) -> Permit:
        count_result = await db.execute(select(func.count()).select_from(Permit))
        next_num = (count_result.scalar() or 0) + 1
        internal_ref = f"PS-{next_num:05d}"

        checklist = PermitStreamEngine._generate_checklist(ahj, permit_type)
        zoning_flags = PermitStreamEngine._assess_zoning_risk(ahj, scope_type)

        permit = Permit(
            job_id=job_id,
            lead_id=lead_id,
            internal_ref=internal_ref,
            permit_type=permit_type,
            status=PermitStatus.INTAKE,
            ahj=ahj,
            property_address=property_address,
            project_description=project_description,
            scope_type=scope_type,
            estimated_cost=estimated_cost,
            square_footage=square_footage,
            checklist_json=json.dumps(checklist),
            zoning_flags=json.dumps(zoning_flags),
            zoning_risk_score=len(zoning_flags) * 15.0,
            completeness_score=0.0,
            deficiency_score=0.0,
            forecast_days_to_issue=PermitStreamEngine._forecast_days(ahj),
        )
        db.add(permit)
        await db.commit()
        await db.refresh(permit)

        logger.info("PermitStream: created %s for %s in %s", internal_ref, property_address, ahj)
        return permit

    @staticmethod
    def _generate_checklist(ahj: str, permit_type: PermitType) -> list[dict[str, Any]]:
        rules = MUNICIPAL_RULES.get(ahj, {})
        checklist = []
        for item in RESIDENTIAL_CHECKLIST:
            entry = {**item, "complete": False}
            if item["item"] == "Conservation Commission approval":
                entry["required"] = rules.get("conservation_overlay", False)
            elif item["item"] == "Historic District Commission approval":
                entry["required"] = rules.get("historic_district", False)
            checklist.append(entry)
        return checklist

    @staticmethod
    def _assess_zoning_risk(ahj: str, scope_type: str | None) -> list[str]:
        rules = MUNICIPAL_RULES.get(ahj, {})
        flags = []
        if rules.get("historic_district"):
            flags.append("historic_district_review")
        if rules.get("conservation_overlay"):
            flags.append("conservation_commission_required")
        if scope_type in ("addition", "new_construction") and rules.get("requires_zba_variance"):
            flags.append("potential_zba_variance")
        return flags

    @staticmethod
    def _forecast_days(ahj: str) -> int:
        rules = MUNICIPAL_RULES.get(ahj, {})
        return rules.get("median_review_days", 30)

    @staticmethod
    async def score_deficiencies(
        permit_id: str, db: AsyncSession
    ) -> dict[str, Any]:
        result = await db.execute(select(Permit).where(Permit.id == permit_id))
        permit = result.scalar_one_or_none()
        if not permit:
            raise ValueError(f"Permit {permit_id} not found")

        checklist = json.loads(permit.checklist_json or "[]")
        required = [c for c in checklist if c.get("required")]
        completed = [c for c in required if c.get("complete")]
        missing = [c for c in required if not c.get("complete")]

        completeness = (len(completed) / len(required) * 100) if required else 100
        deficiency_score = len(missing) * 10.0

        permit.completeness_score = completeness
        permit.deficiency_score = deficiency_score
        permit.deficiency_count = len(missing)

        await db.commit()
        await db.refresh(permit)

        return {
            "permit_id": permit.id,
            "internal_ref": permit.internal_ref,
            "completeness_score": completeness,
            "deficiency_score": deficiency_score,
            "missing_items": [m["item"] for m in missing],
            "total_required": len(required),
            "total_completed": len(completed),
        }

    @staticmethod
    async def transition_status(
        permit_id: str,
        new_status: PermitStatus,
        db: AsyncSession,
    ) -> Permit:
        result = await db.execute(select(Permit).where(Permit.id == permit_id))
        permit = result.scalar_one_or_none()
        if not permit:
            raise ValueError(f"Permit {permit_id} not found")

        now = datetime.now(timezone.utc)
        old_status = permit.status
        permit.status = new_status

        if new_status == PermitStatus.SUBMITTED:
            permit.submitted_at = now
        elif new_status == PermitStatus.APPROVED:
            permit.approved_at = now
        elif new_status == PermitStatus.ISSUED:
            permit.issued_at = now
        elif new_status == PermitStatus.CORRECTIONS:
            permit.correction_rounds += 1

        await db.commit()
        await db.refresh(permit)

        logger.info(
            "PermitStream: %s transitioned %s -> %s",
            permit.internal_ref, old_status.value, new_status.value,
        )
        return permit

    @staticmethod
    async def get_municipal_forecast(
        ahj: str, db: AsyncSession
    ) -> dict[str, Any]:
        rules = MUNICIPAL_RULES.get(ahj, {})

        open_count = await db.execute(
            select(func.count())
            .select_from(Permit)
            .where(Permit.ahj == ahj)
            .where(Permit.status.in_([
                PermitStatus.SUBMITTED, PermitStatus.IN_REVIEW,
                PermitStatus.CORRECTIONS, PermitStatus.RESUBMITTED,
            ]))
        )
        issued_count = await db.execute(
            select(func.count())
            .select_from(Permit)
            .where(Permit.ahj == ahj)
            .where(Permit.status == PermitStatus.ISSUED)
        )

        return {
            "ahj": ahj,
            "median_days": rules.get("median_review_days", 30),
            "p90_days": rules.get("p90_review_days", 60),
            "open": open_count.scalar() or 0,
            "issued_total": issued_count.scalar() or 0,
            "historic_district": rules.get("historic_district", False),
            "conservation_overlay": rules.get("conservation_overlay", False),
            "typical_fees": rules.get("typical_fees", {}),
        }
