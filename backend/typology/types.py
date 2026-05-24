"""
Core Type Definitions for the Typology Intelligence Layer

Deterministic operational typologies that prevent hallucinated categories,
normalize operational data, and provide structured classification intelligence.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal


# ─── Customer Typology ─────────────────────────────────────────────────────────

class CustomerArchetype(str, Enum):
    LUXURY_RENOVATION = "luxury_renovation"
    EMERGENCY_REPAIR = "emergency_repair"
    HISTORIC_PROPERTY = "historic_property"
    COASTAL_BUILD = "coastal_build"
    COMMERCIAL_TENANT_FIT = "commercial_tenant_fit"
    MULTI_FAMILY_DEVELOPER = "multi_family_developer"
    MUNICIPAL_PROJECT = "municipal_project"
    REPEAT_MAINTENANCE = "repeat_maintenance"
    INVESTOR_FLIP = "investor_flip"
    FIRST_TIME_HOMEOWNER = "first_time_homeowner"
    INSURANCE_RESTORATION = "insurance_restoration"
    ADAPTIVE_REUSE = "adaptive_reuse"


class RevenueProfile(str, Enum):
    HIGH_VALUE_SLOW = "high_value_slow"
    FAST_CLOSE = "fast_close"
    RECURRING = "recurring"
    SPECULATIVE = "speculative"
    INSTITUTIONAL = "institutional"


class UrgencyLevel(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    STANDARD = "standard"
    FLEXIBLE = "flexible"
    DORMANT = "dormant"


# ─── Construction Typology ─────────────────────────────────────────────────────

class ProjectType(str, Enum):
    RESIDENTIAL_RENOVATION = "residential_renovation"
    RESIDENTIAL_ADDITION = "residential_addition"
    RESIDENTIAL_NEW = "residential_new"
    COMMERCIAL_FIT_OUT = "commercial_fit_out"
    COMMERCIAL_GROUND_UP = "commercial_ground_up"
    ADAPTIVE_REUSE = "adaptive_reuse"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"


class ProjectComplexity(str, Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"
    HIGH_COMPLEXITY = "high_complexity"


# ─── Permit Typology ──────────────────────────────────────────────────────────

class PermitRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class ZoningOverlay(str, Enum):
    NONE = "none"
    HISTORIC = "historic"
    COASTAL = "coastal"
    WETLANDS = "wetlands"
    FLOOD_ZONE = "flood_zone"
    MIXED_USE = "mixed_use"
    RAILROAD = "railroad"


class PermitType(str, Enum):
    BUILDING_RESIDENTIAL = "building_residential"
    BUILDING_COMMERCIAL = "building_commercial"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    MECHANICAL = "mechanical"
    DEMOLITION = "demolition"
    SIGN = "sign"
    OCCUPANCY = "occupancy"
    SPECIAL_USE = "special_use"


# ─── Compliance Typology ──────────────────────────────────────────────────────

InvestorStatus = Literal[
    "accredited",
    "pending_review",
    "rejected",
    "restricted",
    "suspended",
]

ContractorVerification = Literal[
    "verified",
    "pending_docs",
    "expired_insurance",
    "restricted",
    "blacklisted",
]

class ComplianceLevel(str, Enum):
    FULL = "full"
    CONDITIONAL = "conditional"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


# ─── Operational Lifecycle ─────────────────────────────────────────────────────

class LifecycleStage(str, Enum):
    LEAD = "lead"
    INTAKE = "intake"
    ESTIMATE = "estimate"
    PERMIT = "permit"
    MOBILIZATION = "mobilization"
    PRODUCTION = "production"
    PUNCH = "punch"
    CLOSEOUT = "closeout"
    MAINTENANCE = "maintenance"
    ARCHIVED = "archived"


# ─── Risk Collapse ────────────────────────────────────────────────────────────

class CollapsedRiskCategory(str, Enum):
    """
    Complex multi-factor risk scenarios collapse into simple operational categories.
    E.g. 'Historic-Coastal-Mixed-Zoning-Railroad-Overlay' → HIGH_COMPLEXITY_PROJECT
    """
    ROUTINE = "routine"
    ELEVATED = "elevated"
    HIGH_COMPLEXITY = "high_complexity"
    INSTITUTIONAL_REVIEW = "institutional_review"
