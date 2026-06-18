"""
NoblePort Document Model

Contracts, plans, permits, and attachments. Documents attach to any entity
via a loose (entity_type, entity_id) reference and feed the document-
completeness dimension of the Proof of Trust score.
"""

from enum import Enum as PyEnum

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class DocumentType(str, PyEnum):
    CONTRACT = "contract"
    PLAN = "plan"
    PERMIT = "permit"
    ESTIMATE = "estimate"
    INVOICE = "invoice"
    COI = "coi"
    W9 = "w9"
    INSPECTION_REPORT = "inspection_report"
    PHOTO = "photo"
    OTHER = "other"


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType), default=DocumentType.OTHER, nullable=False
    )

    # Loose polymorphic attachment to any entity (lead, project, contract, ...).
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    uploaded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Document {self.name} ({self.doc_type.value})>"
