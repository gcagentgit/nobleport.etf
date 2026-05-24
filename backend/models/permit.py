"""
NoblePort Permit Model — PermitStream MVP

Tracks residential construction permits through the municipal lifecycle.
Supports deficiency scoring, zoning risk, and submission validation.
"""

from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class PermitStatus(str, PyEnum):
    INTAKE = "intake"
    DRAFTING = "drafting"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    CORRECTIONS = "corrections"
    RESUBMITTED = "resubmitted"
    APPROVED = "approved"
    ISSUED = "issued"
    DENIED = "denied"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class PermitType(str, PyEnum):
    BUILDING = "building"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    MECHANICAL = "mechanical"
    DEMOLITION = "demolition"
    ZONING = "zoning"
    CONSERVATION = "conservation"
    SPECIAL = "special"


class Permit(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "permits"

    job_id: Mapped[str | None] = mapped_column(
        ForeignKey("jobs.id"), nullable=True, index=True
    )
    lead_id: Mapped[str | None] = mapped_column(
        ForeignKey("leads.id"), nullable=True, index=True
    )

    permit_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True
    )
    internal_ref: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )

    permit_type: Mapped[PermitType] = mapped_column(
        Enum(PermitType), default=PermitType.BUILDING, nullable=False
    )
    status: Mapped[PermitStatus] = mapped_column(
        Enum(PermitStatus), default=PermitStatus.INTAKE, nullable=False
    )

    # Municipality (AHJ = Authority Having Jurisdiction)
    ahj: Mapped[str] = mapped_column(String(255), nullable=False)
    ahj_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ahj_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Property
    property_address: Mapped[str] = mapped_column(String(500), nullable=False)
    parcel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    zoning_district: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Scope
    project_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    square_footage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timeline
    submitted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issued_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Scoring (PermitStream intelligence)
    deficiency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    zoning_risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    forecast_days_to_issue: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Deficiencies
    deficiency_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correction_rounds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Zoning flags (JSON-serialized list)
    zoning_flags: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Checklist (JSON-serialized checklist state)
    checklist_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Assigned reviewer
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assigned_agent: Mapped[str | None] = mapped_column(String(100), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Permit {self.internal_ref} {self.ahj} ({self.status.value})>"
