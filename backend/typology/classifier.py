"""
Typology Classifier — Deterministic Classification Engine

Maps raw operational data into structured types. This is not ML-based
fuzzy classification — it is deterministic rule evaluation that produces
consistent, auditable categorization.

This is what makes Stephanie.ai predictive instead of reactive.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.typology.types import (
    CollapsedRiskCategory,
    ComplianceLevel,
    CustomerArchetype,
    PermitRisk,
    ProjectComplexity,
    ProjectType,
    RevenueProfile,
    UrgencyLevel,
    ZoningOverlay,
)


@dataclass(frozen=True)
class ClassificationResult:
    archetype: CustomerArchetype
    revenue_profile: RevenueProfile
    urgency: UrgencyLevel
    project_type: ProjectType
    complexity: ProjectComplexity
    permit_risk: PermitRisk
    collapsed_risk: CollapsedRiskCategory
    confidence: float
    reasoning: tuple[str, ...]


def classify_lead(
    *,
    budget: float,
    property_type: str,
    urgency_signal: str,
    zoning_overlays: list[str],
    is_repeat_client: bool,
    has_historic_designation: bool,
    is_coastal: bool,
    is_commercial: bool,
) -> ClassificationResult:
    """Deterministic lead classification from intake data."""

    # ── Archetype resolution ──
    archetype = _resolve_archetype(
        budget=budget,
        property_type=property_type,
        is_repeat_client=is_repeat_client,
        has_historic_designation=has_historic_designation,
        is_coastal=is_coastal,
        is_commercial=is_commercial,
    )

    # ── Revenue profile ──
    revenue_profile = _resolve_revenue_profile(budget, is_repeat_client, is_commercial)

    # ── Urgency ──
    urgency = _resolve_urgency(urgency_signal)

    # ── Project type ──
    project_type = _resolve_project_type(property_type, is_commercial)

    # ── Permit risk ──
    overlays = [ZoningOverlay(o) for o in zoning_overlays if o in ZoningOverlay.__members__.values()]
    permit_risk = _resolve_permit_risk(overlays, has_historic_designation, is_coastal)

    # ── Complexity ──
    complexity = _resolve_complexity(permit_risk, budget, len(overlays))

    # ── Collapsed risk ──
    collapsed_risk = _collapse_risk(permit_risk, complexity)

    reasoning = _build_reasoning(archetype, permit_risk, complexity, overlays)

    return ClassificationResult(
        archetype=archetype,
        revenue_profile=revenue_profile,
        urgency=urgency,
        project_type=project_type,
        complexity=complexity,
        permit_risk=permit_risk,
        collapsed_risk=collapsed_risk,
        confidence=0.92 if len(overlays) <= 1 else 0.78,
        reasoning=reasoning,
    )


# ─── Resolution Functions ──────────────────────────────────────────────────────


def _resolve_archetype(
    *,
    budget: float,
    property_type: str,
    is_repeat_client: bool,
    has_historic_designation: bool,
    is_coastal: bool,
    is_commercial: bool,
) -> CustomerArchetype:
    if is_repeat_client:
        return CustomerArchetype.REPEAT_MAINTENANCE
    if has_historic_designation:
        return CustomerArchetype.HISTORIC_PROPERTY
    if is_coastal:
        return CustomerArchetype.COASTAL_BUILD
    if is_commercial:
        return CustomerArchetype.COMMERCIAL_TENANT_FIT
    if budget > 2_000_000:
        return CustomerArchetype.LUXURY_RENOVATION
    if budget > 500_000:
        return CustomerArchetype.MULTI_FAMILY_DEVELOPER
    return CustomerArchetype.FIRST_TIME_HOMEOWNER


def _resolve_revenue_profile(budget: float, is_repeat: bool, is_commercial: bool) -> RevenueProfile:
    if is_repeat:
        return RevenueProfile.RECURRING
    if is_commercial:
        return RevenueProfile.INSTITUTIONAL
    if budget > 1_500_000:
        return RevenueProfile.HIGH_VALUE_SLOW
    return RevenueProfile.FAST_CLOSE


def _resolve_urgency(signal: str) -> UrgencyLevel:
    mapping = {
        "emergency": UrgencyLevel.EMERGENCY,
        "urgent": UrgencyLevel.URGENT,
        "asap": UrgencyLevel.URGENT,
        "standard": UrgencyLevel.STANDARD,
        "flexible": UrgencyLevel.FLEXIBLE,
        "no_rush": UrgencyLevel.FLEXIBLE,
        "dormant": UrgencyLevel.DORMANT,
    }
    return mapping.get(signal.lower(), UrgencyLevel.STANDARD)


def _resolve_project_type(property_type: str, is_commercial: bool) -> ProjectType:
    if is_commercial:
        return ProjectType.COMMERCIAL_FIT_OUT
    mapping = {
        "renovation": ProjectType.RESIDENTIAL_RENOVATION,
        "addition": ProjectType.RESIDENTIAL_ADDITION,
        "new_construction": ProjectType.RESIDENTIAL_NEW,
        "adaptive_reuse": ProjectType.ADAPTIVE_REUSE,
        "maintenance": ProjectType.MAINTENANCE,
        "emergency": ProjectType.EMERGENCY,
    }
    return mapping.get(property_type.lower(), ProjectType.RESIDENTIAL_RENOVATION)


def _resolve_permit_risk(
    overlays: list[ZoningOverlay],
    has_historic: bool,
    is_coastal: bool,
) -> PermitRisk:
    risk_score = len(overlays)
    if has_historic:
        risk_score += 2
    if is_coastal:
        risk_score += 2
    if ZoningOverlay.FLOOD_ZONE in overlays:
        risk_score += 1
    if ZoningOverlay.WETLANDS in overlays:
        risk_score += 1

    if risk_score >= 5:
        return PermitRisk.EXTREME
    if risk_score >= 3:
        return PermitRisk.HIGH
    if risk_score >= 1:
        return PermitRisk.MEDIUM
    return PermitRisk.LOW


def _resolve_complexity(
    permit_risk: PermitRisk,
    budget: float,
    overlay_count: int,
) -> ProjectComplexity:
    if permit_risk == PermitRisk.EXTREME or (budget > 5_000_000 and overlay_count > 2):
        return ProjectComplexity.HIGH_COMPLEXITY
    if permit_risk == PermitRisk.HIGH or budget > 2_000_000:
        return ProjectComplexity.COMPLEX
    if permit_risk == PermitRisk.MEDIUM or budget > 500_000:
        return ProjectComplexity.STANDARD
    return ProjectComplexity.SIMPLE


def _collapse_risk(permit_risk: PermitRisk, complexity: ProjectComplexity) -> CollapsedRiskCategory:
    if complexity == ProjectComplexity.HIGH_COMPLEXITY:
        return CollapsedRiskCategory.INSTITUTIONAL_REVIEW
    if permit_risk in (PermitRisk.HIGH, PermitRisk.EXTREME):
        return CollapsedRiskCategory.HIGH_COMPLEXITY
    if complexity == ProjectComplexity.COMPLEX or permit_risk == PermitRisk.MEDIUM:
        return CollapsedRiskCategory.ELEVATED
    return CollapsedRiskCategory.ROUTINE


def _build_reasoning(
    archetype: CustomerArchetype,
    permit_risk: PermitRisk,
    complexity: ProjectComplexity,
    overlays: list[ZoningOverlay],
) -> tuple[str, ...]:
    reasons: list[str] = [f"Archetype: {archetype.value}"]
    if overlays:
        reasons.append(f"Overlays: {', '.join(o.value for o in overlays)}")
    reasons.append(f"Permit risk: {permit_risk.value}")
    reasons.append(f"Complexity: {complexity.value}")
    return tuple(reasons)
