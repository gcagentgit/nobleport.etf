"""
NoblePort Subcontractor Model

A trade partner performing work on a project. Compliance fields (COI, W-9,
license, insurance expiry) gate participation and feed the Financial layer's
contractor-payment controls.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import BuildertrendSyncMixin, TimestampMixin, UUIDMixin


class SubcontractorStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_COMPLIANCE = "pending_compliance"
    SUSPENDED = "suspended"


class Subcontractor(Base, UUIDMixin, TimestampMixin, BuildertrendSyncMixin):
    __tablename__ = "subcontractors"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    status: Mapped[SubcontractorStatus] = mapped_column(
        Enum(SubcontractorStatus),
        default=SubcontractorStatus.PENDING_COMPLIANCE,
        nullable=False,
    )

    license_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    insurance_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    coi_on_file: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    w9_on_file: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def compliant(self) -> bool:
        """A sub is payment-eligible only with COI + W-9 on file."""
        return self.coi_on_file and self.w9_on_file

    def __repr__(self) -> str:
        return f"<Subcontractor {self.name} / {self.trade} ({self.status.value})>"
