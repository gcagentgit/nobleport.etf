"""
Typology Engine API

Exposes the classification, normalization, taxonomy, and analytics
capabilities of the Typology Intelligence Layer.

Routes:
  /api/v1/typology-engine/classify     — Classify a lead from intake data
  /api/v1/typology-engine/normalize    — Normalize a raw label
  /api/v1/typology-engine/taxonomy     — Browse hierarchical taxonomies
  /api/v1/typology-engine/entropy      — Operational entropy metrics
  /api/v1/typology-engine/coverage     — Coverage gap detection
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.typology.analytics import (
    compute_entropy,
    detect_coverage_gaps,
)
from backend.typology.classifier import classify_lead
from backend.typology.normalizer import (
    normalize_client,
    normalize_permit_status,
    normalize_project,
)
from backend.typology.taxonomy import (
    CONTRACTOR_TAXONOMY,
    PERMIT_TAXONOMY,
    PROJECT_TAXONOMY,
    flatten_taxonomy,
    get_taxonomy_depth,
)
from backend.typology.types import CustomerArchetype, ProjectType

router = APIRouter()


# ─── Classification ────────────────────────────────────────────────────────────


class ClassifyLeadRequest(BaseModel):
    budget: float
    property_type: str
    urgency_signal: str = "standard"
    zoning_overlays: list[str] = []
    is_repeat_client: bool = False
    has_historic_designation: bool = False
    is_coastal: bool = False
    is_commercial: bool = False


@router.post("/classify")
async def classify(request: ClassifyLeadRequest) -> dict[str, Any]:
    """Classify a lead into deterministic operational types."""
    result = classify_lead(
        budget=request.budget,
        property_type=request.property_type,
        urgency_signal=request.urgency_signal,
        zoning_overlays=request.zoning_overlays,
        is_repeat_client=request.is_repeat_client,
        has_historic_designation=request.has_historic_designation,
        is_coastal=request.is_coastal,
        is_commercial=request.is_commercial,
    )
    return {
        "archetype": result.archetype.value,
        "revenue_profile": result.revenue_profile.value,
        "urgency": result.urgency.value,
        "project_type": result.project_type.value,
        "complexity": result.complexity.value,
        "permit_risk": result.permit_risk.value,
        "collapsed_risk": result.collapsed_risk.value,
        "confidence": result.confidence,
        "reasoning": list(result.reasoning),
    }


# ─── Normalization ─────────────────────────────────────────────────────────────


@router.get("/normalize")
async def normalize(
    value: str = Query(..., description="Raw label to normalize"),
    domain: str = Query("client", pattern="^(client|project|permit_status)$"),
) -> dict[str, str]:
    """Normalize a fuzzy operational label to its canonical form."""
    if domain == "client":
        canonical = normalize_client(value)
    elif domain == "project":
        canonical = normalize_project(value)
    else:
        canonical = normalize_permit_status(value)

    return {
        "input": value,
        "canonical": canonical,
        "domain": domain,
        "changed": str(canonical != value).lower(),
    }


# ─── Taxonomy ──────────────────────────────────────────────────────────────────


@router.get("/taxonomy")
async def get_taxonomy(
    domain: str = Query("project", pattern="^(project|permit|contractor)$"),
) -> dict[str, Any]:
    """Browse hierarchical taxonomy structures."""
    root = {
        "project": PROJECT_TAXONOMY,
        "permit": PERMIT_TAXONOMY,
        "contractor": CONTRACTOR_TAXONOMY,
    }[domain]

    def serialize(node) -> dict[str, Any]:
        result: dict[str, Any] = {"id": node.id, "label": node.label}
        if node.children:
            result["children"] = [serialize(c) for c in node.children]
        return result

    return {
        "domain": domain,
        "depth": get_taxonomy_depth(root),
        "total_nodes": len(flatten_taxonomy(root)),
        "tree": serialize(root),
    }


# ─── Analytics ─────────────────────────────────────────────────────────────────


@router.get("/entropy")
async def get_entropy() -> dict[str, Any]:
    """
    Operational type entropy — measures business predictability.
    Low entropy = concentrated, predictable pipeline.
    High entropy = diverse, potentially unstable intake.
    """
    # Deterministic fixture representing current pipeline type distribution
    current_distribution = {
        "residential_renovation": 14,
        "residential_addition": 8,
        "residential_new": 3,
        "commercial_fit_out": 5,
        "adaptive_reuse": 2,
        "maintenance": 6,
        "emergency": 1,
        "municipal_project": 2,
    }

    summary = compute_entropy(current_distribution)
    return {
        "entropy": summary.entropy,
        "max_entropy": summary.max_entropy,
        "normalized": summary.normalized,
        "interpretation": summary.interpretation,
        "dominant_type": summary.dominant_type,
        "dominant_share": summary.dominant_share,
        "distribution": current_distribution,
    }


@router.get("/coverage")
async def get_coverage_gaps() -> dict[str, Any]:
    """Detect operational blind spots — expected types with no representation."""
    current_counts = {
        "luxury_renovation": 3,
        "emergency_repair": 1,
        "historic_property": 2,
        "coastal_build": 4,
        "commercial_tenant_fit": 2,
        "multi_family_developer": 0,
        "municipal_project": 1,
        "repeat_maintenance": 5,
        "investor_flip": 0,
        "first_time_homeowner": 6,
        "insurance_restoration": 0,
        "adaptive_reuse": 1,
    }

    expected = [a.value for a in CustomerArchetype]
    gaps = detect_coverage_gaps(current_counts, expected, minimum_threshold=1)

    return {
        "total_types": len(expected),
        "covered": len(expected) - len(gaps),
        "gaps": [
            {
                "type": g.type_name,
                "actual": g.actual_count,
                "minimum_expected": g.expected_minimum,
                "severity": g.severity,
            }
            for g in gaps
        ],
        "coverage_pct": round((len(expected) - len(gaps)) / len(expected) * 100, 1),
    }
