"""
NoblePort Sales API

Read-only endpoints over the v2.0 sales-intelligence engine: the revenue
hierarchy, the GPPI leaderboard, the 80/20 profitable-lead routing, and the
SIMULATED team simulation. Every simulation response carries its Truth-Layer
tag — these inform human resource-allocation decisions, they do not make them.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.sales import (
    GPPI_WEIGHTS,
    REVENUE_HIERARCHY,
    aggregate,
    hierarchy_view,
    metric_groups,
    run_simulation,
)

router = APIRouter()


@router.get("/hierarchy")
async def get_hierarchy():
    """The NoblePort revenue hierarchy: 13 service lines across 4 strategic tiers."""
    return {
        "tiers": hierarchy_view(),
        "lines": [
            {
                "key": l.key,
                "name": l.name,
                "tier": int(l.tier),
                "rank": l.rank,
                "lead_feeder": l.lead_feeder,
                "typical_job_low": l.typical_job_low,
                "typical_job_high": l.typical_job_high,
            }
            for l in REVENUE_HIERARCHY
        ],
    }


@router.get("/metrics")
async def get_metric_catalog():
    """The v1 sales dashboard metric catalog, grouped by lead/sales/financial."""
    return {"metric_groups": metric_groups()}


@router.get("/leaderboard")
async def get_leaderboard(
    team_size: int = Query(8, ge=1, le=12),
    seed: int = Query(42, ge=0),
):
    """The GPPI leaderboard for a SIMULATED team of the given size."""
    sim = run_simulation(team_size=team_size, lead_count=0, seed=seed)
    return {
        "truth_tag": sim.truth_tag.value,
        "label": "SIMULATED MODEL OUTPUT",
        "weights": {k.value: v for k, v in GPPI_WEIGHTS.items()},
        "leaderboard": [s.to_dict() for s in sim.leaderboard],
    }


@router.get("/routing")
async def get_routing(
    team_size: int = Query(8, ge=1, le=12),
    lead_count: int = Query(40, ge=0, le=500),
    seed: int = Query(42, ge=0),
):
    """The 80/20 profitable-lead routing plan for a SIMULATED team and lead board."""
    sim = run_simulation(team_size=team_size, lead_count=lead_count, seed=seed)
    return {
        "truth_tag": sim.truth_tag.value,
        "label": "SIMULATED MODEL OUTPUT",
        "routing": sim.routing.to_dict(),
    }


@router.get("/simulation")
async def get_simulation(
    team_size: int = Query(8, ge=1, le=12),
    lead_count: int = Query(40, ge=0, le=500),
    months_of_real_data: float = Query(0.0, ge=0.0),
    seed: int = Query(42, ge=0),
):
    """A full SIMULATED sales snapshot: leaderboard + routing + data-readiness gate."""
    sim = run_simulation(
        team_size=team_size,
        lead_count=lead_count,
        months_of_real_data=months_of_real_data,
        seed=seed,
    )
    return sim.to_dict()


@router.get("/dashboard")
async def get_dashboard(
    team_size: int = Query(8, ge=1, le=12),
    lead_count: int = Query(40, ge=0, le=500),
    months_of_real_data: float = Query(0.0, ge=0.0),
    seed: int = Query(42, ge=0),
):
    """The aggregated v1 sales dashboard payload over a SIMULATED snapshot."""
    sim = run_simulation(
        team_size=team_size,
        lead_count=lead_count,
        months_of_real_data=months_of_real_data,
        seed=seed,
    )
    return aggregate(sim)
