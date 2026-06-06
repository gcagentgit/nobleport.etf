"""
NoblePort Contacts Service

Master CRM directory operations.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.contacts.models import (
    Contact,
    ContactInteraction,
    ContactRelationship,
    InteractionDirection,
    InteractionType,
    RelationshipType,
)


class ContactsService:
    """Operations against the master contact directory."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def create_contact(self, **fields: Any) -> Contact:
        contact = Contact(**fields)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def find_or_create(
        self,
        email: str | None = None,
        phone: str | None = None,
        **defaults: Any,
    ) -> tuple[Contact, bool]:
        """Lookup by email or phone, otherwise create. Returns (contact, created)."""
        if not (email or phone):
            raise ValueError("find_or_create requires email or phone")

        clauses = []
        if email:
            clauses.append(Contact.email == email)
        if phone:
            clauses.append(Contact.phone == phone)

        stmt = select(Contact).where(or_(*clauses)).limit(1)
        existing = (await self.db.execute(stmt)).scalars().first()
        if existing:
            return existing, False

        defaults.setdefault("first_name", defaults.pop("first_name", None) or "Unknown")
        defaults.setdefault("last_name", defaults.pop("last_name", None) or "Unknown")
        contact = Contact(email=email, phone=phone, **defaults)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact, True

    async def get(self, contact_id: str) -> Contact:
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")
        return contact

    async def list_contacts(self, limit: int = 100) -> list[Contact]:
        stmt = select(Contact).order_by(Contact.updated_at.desc()).limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())

    async def update(self, contact_id: str, updates: dict[str, Any]) -> Contact:
        contact = await self.get(contact_id)
        for key, value in updates.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    # ------------------------------------------------------------------
    # Merge / DNC
    # ------------------------------------------------------------------
    async def merge_duplicates(self, primary_id: str, duplicate_id: str) -> Contact:
        """Move all history from duplicate -> primary, delete duplicate."""
        if primary_id == duplicate_id:
            raise ValueError("Cannot merge a contact into itself")
        primary = await self.get(primary_id)
        duplicate = await self.get(duplicate_id)

        stmt = select(ContactInteraction).where(
            ContactInteraction.contact_id == duplicate.id
        )
        for interaction in (await self.db.execute(stmt)).scalars().all():
            interaction.contact_id = primary.id

        rel_stmt = select(ContactRelationship).where(
            or_(
                ContactRelationship.contact_id_a == duplicate.id,
                ContactRelationship.contact_id_b == duplicate.id,
            )
        )
        for rel in (await self.db.execute(rel_stmt)).scalars().all():
            if rel.contact_id_a == duplicate.id:
                rel.contact_id_a = primary.id
            if rel.contact_id_b == duplicate.id:
                rel.contact_id_b = primary.id

        # Backfill any missing fields on primary from duplicate
        for field in ("email", "phone", "company", "role", "hubspot_id"):
            if not getattr(primary, field) and getattr(duplicate, field):
                setattr(primary, field, getattr(duplicate, field))

        merge_note = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] merged from {duplicate.id}"
        primary.notes = f"{primary.notes}\n{merge_note}" if primary.notes else merge_note

        await self.db.delete(duplicate)
        await self.db.commit()
        await self.db.refresh(primary)
        return primary

    async def mark_dnc(self, contact_id: str, reason: str) -> Contact:
        contact = await self.get(contact_id)
        contact.do_not_contact = True
        contact.dnc_reason = reason
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------
    async def log_interaction(
        self,
        contact_id: str,
        interaction_type: str,
        direction: str,
        summary: str | None = None,
        full_content: str | None = None,
        recorded_by: str | None = None,
        related_lead_id: str | None = None,
        related_job_id: str | None = None,
        occurred_at: datetime | None = None,
    ) -> ContactInteraction:
        await self.get(contact_id)  # validate exists
        interaction = ContactInteraction(
            contact_id=contact_id,
            interaction_type=InteractionType(interaction_type),
            direction=InteractionDirection(direction),
            summary=summary,
            full_content=full_content,
            recorded_by=recorded_by,
            related_lead_id=related_lead_id,
            related_job_id=related_job_id,
            occurred_at=occurred_at or datetime.now(timezone.utc),
        )
        self.db.add(interaction)
        await self.db.commit()
        await self.db.refresh(interaction)
        return interaction

    async def get_history(self, contact_id: str) -> list[ContactInteraction]:
        await self.get(contact_id)
        stmt = (
            select(ContactInteraction)
            .where(ContactInteraction.contact_id == contact_id)
            .order_by(ContactInteraction.occurred_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    # ------------------------------------------------------------------
    # Search / relationships
    # ------------------------------------------------------------------
    async def search(self, query: str, limit: int = 50) -> list[Contact]:
        like = f"%{query}%"
        stmt = (
            select(Contact)
            .where(
                or_(
                    Contact.first_name.ilike(like),
                    Contact.last_name.ilike(like),
                    Contact.email.ilike(like),
                    Contact.phone.ilike(like),
                    Contact.company.ilike(like),
                )
            )
            .limit(limit)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def add_relationship(
        self, a_id: str, b_id: str, relationship_type: str
    ) -> ContactRelationship:
        if a_id == b_id:
            raise ValueError("Cannot relate a contact to itself")
        await self.get(a_id)
        await self.get(b_id)
        rel = ContactRelationship(
            contact_id_a=a_id,
            contact_id_b=b_id,
            relationship_type=RelationshipType(relationship_type),
        )
        self.db.add(rel)
        await self.db.commit()
        await self.db.refresh(rel)
        return rel
