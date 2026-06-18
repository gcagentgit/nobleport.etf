"""
NoblePort Equipment Model

Owned and rented equipment. Costs roll up into the Accounting layer; current
assignment supports Project Operations and Field Operations.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class EquipmentOwnership(str, PyEnum):
    OWNED = "owned"
    RENTED = "rented"
    LEASED = "leased"


class EquipmentStatus(str, PyEnum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class Equipment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "equipment"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_tag: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    ownership: Mapped[EquipmentOwnership] = mapped_column(
        Enum(EquipmentOwnership), default=EquipmentOwnership.OWNED, nullable=False
    )
    status: Mapped[EquipmentStatus] = mapped_column(
        Enum(EquipmentStatus), default=EquipmentStatus.AVAILABLE, nullable=False
    )

    # Current assignment (loose ref to a project/job)
    assigned_to: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    purchase_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    purchase_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    hourly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Equipment {self.name} ({self.status.value})>"
