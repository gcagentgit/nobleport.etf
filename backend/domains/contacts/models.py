"""
NoblePort Contacts Models

Master CRM contact directory, interaction log, and contact relationships.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class InteractionType(str, PyEnum):
    EMAIL = "email"
    CALL = "call"
    SMS = "sms"
    MEETING = "meeting"
    SITE_VISIT = "site_visit"
    NOTE = "note"


class InteractionDirection(str, PyEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class RelationshipType(str, PyEnum):
    SPOUSE = "spouse"
    BUSINESS_PARTNER = "business_partner"
    REFERRER = "referrer"
    REFERRED_BY = "referred_by"
    COLLEAGUE = "colleague"


class Contact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contacts"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-as-text
    do_not_contact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dnc_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    hubspot_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<Contact {self.first_name} {self.last_name}>"


class ContactInteraction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contact_interactions"

    contact_id: Mapped[str] = mapped_column(
        ForeignKey("contacts.id"), nullable=False, index=True
    )
    interaction_type: Mapped[InteractionType] = mapped_column(
        Enum(InteractionType), nullable=False
    )
    direction: Mapped[InteractionDirection] = mapped_column(
        Enum(InteractionDirection), nullable=False
    )
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    full_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    recorded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    related_lead_id: Mapped[str | None] = mapped_column(
        ForeignKey("leads.id"), nullable=True, index=True
    )
    related_job_id: Mapped[str | None] = mapped_column(
        ForeignKey("jobs.id"), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<ContactInteraction {self.interaction_type.value} {self.direction.value}>"


class ContactRelationship(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contact_relationships"

    contact_id_a: Mapped[str] = mapped_column(
        ForeignKey("contacts.id"), nullable=False, index=True
    )
    contact_id_b: Mapped[str] = mapped_column(
        ForeignKey("contacts.id"), nullable=False, index=True
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ContactRelationship {self.contact_id_a}-{self.relationship_type.value}->{self.contact_id_b}>"
