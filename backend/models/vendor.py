"""
NoblePort Vendor Model

A material or service supplier paid through the Financial layer (Payment Node)
and tracked as cost of goods in the Accounting layer.
"""

from enum import Enum as PyEnum

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import BuildertrendSyncMixin, TimestampMixin, UUIDMixin


class VendorCategory(str, PyEnum):
    MATERIAL = "material"
    EQUIPMENT = "equipment"
    SERVICE = "service"
    UTILITY = "utility"
    OTHER = "other"


class VendorStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_HOLD = "on_hold"


class Vendor(Base, UUIDMixin, TimestampMixin, BuildertrendSyncMixin):
    __tablename__ = "vendors"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    category: Mapped[VendorCategory] = mapped_column(
        Enum(VendorCategory), default=VendorCategory.MATERIAL, nullable=False
    )
    status: Mapped[VendorStatus] = mapped_column(
        Enum(VendorStatus), default=VendorStatus.ACTIVE, nullable=False
    )

    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Vendor {self.name} ({self.status.value})>"
