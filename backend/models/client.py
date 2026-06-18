"""
NoblePort Client Model

A person or organization NoblePort does business with — the root of the
customer relationship that NobleNest and the Revenue layer build on.
"""

from enum import Enum as PyEnum

from sqlalchemy import Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import BuildertrendSyncMixin, TimestampMixin, UUIDMixin


class ClientType(str, PyEnum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    DEVELOPER = "developer"
    MUNICIPAL = "municipal"
    OTHER = "other"


class ClientStatus(str, PyEnum):
    PROSPECT = "prospect"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Client(Base, UUIDMixin, TimestampMixin, BuildertrendSyncMixin):
    __tablename__ = "clients"

    # Identity
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Classification
    type: Mapped[ClientType] = mapped_column(
        Enum(ClientType), default=ClientType.RESIDENTIAL, nullable=False
    )
    status: Mapped[ClientStatus] = mapped_column(
        Enum(ClientStatus), default=ClientStatus.PROSPECT, nullable=False
    )
    trust_fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Billing address
    billing_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        label = self.company or f"{self.first_name or ''} {self.last_name or ''}".strip()
        return f"<Client {label} ({self.status.value})>"
