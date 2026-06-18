"""
NoblePort Contract Model

An executed agreement binding scope, price, and terms. Contracts carry the
HIC registration reference the Financial layer requires before any payment is
released.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import BuildertrendSyncMixin, TimestampMixin, UUIDMixin


class ContractType(str, PyEnum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    DESIGN_BUILD = "design_build"
    MAINTENANCE = "maintenance"
    OTHER = "other"


class ContractStatus(str, PyEnum):
    DRAFT = "draft"
    SENT = "sent"
    SIGNED = "signed"
    EXECUTED = "executed"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class Contract(Base, UUIDMixin, TimestampMixin, BuildertrendSyncMixin):
    __tablename__ = "contracts"

    contract_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Relationships (string refs; FKs kept loose to match existing models)
    client_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    estimate_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    type: Mapped[ContractType] = mapped_column(
        Enum(ContractType), default=ContractType.RESIDENTIAL, nullable=False
    )
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus), default=ContractStatus.DRAFT, nullable=False
    )

    contract_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    retention_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    # HIC compliance (Massachusetts Home Improvement Contractor registration)
    hic_registration: Mapped[str | None] = mapped_column(String(100), nullable=True)

    signed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Contract {self.contract_number or self.id} ({self.status.value})>"
