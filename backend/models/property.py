"""
NoblePort Property Model

A physical address and its system records. The Customer layer (NobleNest)
tracks per-system condition (roof, siding, windows, HVAC, electrical,
plumbing, paint) so maintenance and upgrade opportunities can be surfaced.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class PropertyType(str, PyEnum):
    SINGLE_FAMILY = "single_family"
    MULTI_FAMILY = "multi_family"
    COMMERCIAL = "commercial"
    LAND = "land"
    MIXED_USE = "mixed_use"
    OTHER = "other"


class Property(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "properties"

    # Owning client (loose ref to match existing model conventions)
    client_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    type: Mapped[PropertyType] = mapped_column(
        Enum(PropertyType), default=PropertyType.SINGLE_FAMILY, nullable=False
    )
    year_built: Mapped[int | None] = mapped_column(String(4), nullable=True)
    square_feet: Mapped[float | None] = mapped_column(Float, nullable=True)

    # NobleNest per-system records (last service / condition notes as free text).
    roof: Mapped[str | None] = mapped_column(Text, nullable=True)
    siding: Mapped[str | None] = mapped_column(Text, nullable=True)
    windows: Mapped[str | None] = mapped_column(Text, nullable=True)
    hvac: Mapped[str | None] = mapped_column(Text, nullable=True)
    electrical: Mapped[str | None] = mapped_column(Text, nullable=True)
    plumbing: Mapped[str | None] = mapped_column(Text, nullable=True)
    paint_history: Mapped[str | None] = mapped_column(Text, nullable=True)

    last_service_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Property {self.address} ({self.type.value})>"
