"""
Category Normalization Engine

Maps fuzzy, inconsistent operational labels into canonical types.
This prevents analytics pollution from synonymous categories.

Example:
  "VIP Client" / "Luxury Client" / "Premium Client" → HIGH_VALUE_CLIENT

Without normalization, every dashboard metric becomes unreliable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizationRule:
    canonical: str
    variants: frozenset[str]


# ─── Client Labels ─────────────────────────────────────────────────────────────

CLIENT_NORMALIZATIONS: tuple[NormalizationRule, ...] = (
    NormalizationRule(
        canonical="HIGH_VALUE_CLIENT",
        variants=frozenset([
            "vip client", "luxury client", "premium client",
            "high-end client", "top-tier client", "whale",
        ]),
    ),
    NormalizationRule(
        canonical="REPEAT_CLIENT",
        variants=frozenset([
            "repeat client", "returning client", "existing client",
            "previous client", "loyal client", "recurring",
        ]),
    ),
    NormalizationRule(
        canonical="INSTITUTIONAL_CLIENT",
        variants=frozenset([
            "institutional", "corporate", "developer",
            "investment group", "fund", "lp", "commercial client",
        ]),
    ),
    NormalizationRule(
        canonical="EMERGENCY_CLIENT",
        variants=frozenset([
            "emergency", "urgent", "asap", "rush",
            "immediate", "critical", "disaster",
        ]),
    ),
    NormalizationRule(
        canonical="FIRST_TIME_CLIENT",
        variants=frozenset([
            "new client", "first time", "new lead",
            "first-time homeowner", "new customer",
        ]),
    ),
)

# ─── Project Labels ────────────────────────────────────────────────────────────

PROJECT_NORMALIZATIONS: tuple[NormalizationRule, ...] = (
    NormalizationRule(
        canonical="RENOVATION",
        variants=frozenset([
            "renovation", "reno", "remodel", "rehab",
            "update", "refresh", "modernization",
        ]),
    ),
    NormalizationRule(
        canonical="ADDITION",
        variants=frozenset([
            "addition", "extension", "expansion",
            "add-on", "buildout", "bump-out",
        ]),
    ),
    NormalizationRule(
        canonical="NEW_CONSTRUCTION",
        variants=frozenset([
            "new construction", "new build", "ground-up",
            "from scratch", "greenfield", "new home",
        ]),
    ),
    NormalizationRule(
        canonical="MAINTENANCE",
        variants=frozenset([
            "maintenance", "repair", "fix", "patch",
            "service call", "upkeep", "preventive",
        ]),
    ),
)

# ─── Permit Status Labels ──────────────────────────────────────────────────────

PERMIT_STATUS_NORMALIZATIONS: tuple[NormalizationRule, ...] = (
    NormalizationRule(
        canonical="SUBMITTED",
        variants=frozenset([
            "submitted", "filed", "sent", "applied",
            "in queue", "pending intake",
        ]),
    ),
    NormalizationRule(
        canonical="IN_REVIEW",
        variants=frozenset([
            "in review", "under review", "being reviewed",
            "assigned", "examiner assigned", "plan review",
        ]),
    ),
    NormalizationRule(
        canonical="CORRECTIONS_REQUIRED",
        variants=frozenset([
            "corrections", "revisions needed", "resubmit",
            "deficient", "incomplete", "rejected for corrections",
        ]),
    ),
    NormalizationRule(
        canonical="APPROVED",
        variants=frozenset([
            "approved", "issued", "granted", "permit issued",
            "ready for pickup", "finalized",
        ]),
    ),
    NormalizationRule(
        canonical="DENIED",
        variants=frozenset([
            "denied", "rejected", "refused", "not approved",
            "disapproved",
        ]),
    ),
)


def normalize(value: str, rules: tuple[NormalizationRule, ...]) -> str:
    """Map a raw label to its canonical form. Returns original if no match."""
    lower = value.lower().strip()
    for rule in rules:
        if lower in rule.variants or lower == rule.canonical.lower():
            return rule.canonical
    return value


def normalize_client(label: str) -> str:
    return normalize(label, CLIENT_NORMALIZATIONS)


def normalize_project(label: str) -> str:
    return normalize(label, PROJECT_NORMALIZATIONS)


def normalize_permit_status(label: str) -> str:
    return normalize(label, PERMIT_STATUS_NORMALIZATIONS)


def get_all_canonical_types(rules: tuple[NormalizationRule, ...]) -> list[str]:
    return [r.canonical for r in rules]
