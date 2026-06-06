"""
NoblePort Contacts Domain

Central CRM directory of every person NoblePort has ever talked to,
plus their interaction history and inter-contact relationships.
"""

from backend.domains.contacts.models import (
    Contact,
    ContactInteraction,
    ContactRelationship,
)
from backend.domains.contacts.routes import router
from backend.domains.contacts.service import ContactsService

__all__ = [
    "Contact",
    "ContactInteraction",
    "ContactRelationship",
    "ContactsService",
    "router",
]
