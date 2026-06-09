"""
Tests for the NoblePort v2.0 sales-intelligence engine.

These assert the model's hard guarantees: GPPI weights sum to 1.0 and are
applied as documented, the heaviest-weighted KPI dominates ranking, the
revenue hierarchy orders ADUs above bathrooms, the 80/20 rule sends premium
leads to top performers, the simulation is deterministic and carries the
SIMULATED truth tag, and the data-readiness gate transitions on schedule.
"""

from __future__ import annotations

from backend.governance.truth_layer import TruthTag
from backend.sales import (
    GPPI_WEIGHTS,
    Lead,
    LeadGrade,
    RepStats,
    RevenueTier,
    SimulationMode,
    aggregate,
    grade_lead,
    profitability_score,
    route_leads,
    run_simulation,
    score_cohort,
    tier_of,
)
from backend.sales.gppi import GppiKpi


# ---------------------------------------------------------------------------
# GPPI
# ---------------------------------------------------------------------------

def test_gppi_weights_sum_to_one():
    assert abs(sum(GPPI_WEIGHTS.values()) - 1.0) < 1e-9


def test_gppi_weights_match_spec():
    assert GPPI_WEIGHTS[GppiKpi.GROSS_PROFIT] == 0.40
    assert GPPI_WEIGHTS[GppiKpi.REVENUE] == 0.25
    assert GPPI_WEIGHTS[GppiKpi.AVG_JOB_SIZE] == 0.15
    assert GPPI_WEIGHTS[GppiKpi.CLOSE_RATE] == 0.10
    assert GPPI_WEIGHTS[GppiKpi.LEAD_RESPONSE_TIME] == 0.05
    assert GPPI_WEIGHTS[GppiKpi.CUSTOMER_SATISFACTION] == 0.05


def _rep(rep_id: str, gp: float, rev: float, jobs: int, opps: int,
         resp: float, csat: float) -> RepStats:
    return RepStats(
        rep_id=rep_id, name=rep_id, gross_profit=gp, revenue=rev,
        jobs_won=jobs, opportunities=opps, lead_response_hours=resp,
        customer_satisfaction=csat,
    )


def test_high_gross_profit_rep_outranks_high_volume_rep():
    """The v2.0 thesis: one ADU at $325k beats two bathrooms at $15k."""
    adu_closer = _rep("adu", gp=110_000, rev=325_000, jobs=1, opps=2, resp=2.0, csat=4.8)
    bath_closer = _rep("bath", gp=9_000, rev=30_000, jobs=2, opps=3, resp=2.0, csat=4.8)
    ranked = score_cohort([adu_closer, bath_closer])
    assert ranked[0].rep_id == "adu"
    assert ranked[0].rank == 1
    assert ranked[1].rep_id == "bath"


def test_close_rate_alone_does_not_win():
    """A perfect close rate on tiny jobs loses to big gross profit (v1 -> v2 fix)."""
    perfect_closer = _rep("perfect", gp=12_000, rev=40_000, jobs=5, opps=5, resp=1.0, csat=5.0)
    big_gp = _rep("big", gp=200_000, rev=600_000, jobs=3, opps=8, resp=8.0, csat=4.0)
    ranked = score_cohort([perfect_closer, big_gp])
    assert ranked[0].rep_id == "big"


def test_lead_response_time_is_inverted():
    """Faster response should score higher on that KPI."""
    fast = _rep("fast", gp=50_000, rev=150_000, jobs=2, opps=4, resp=0.5, csat=4.5)
    slow = _rep("slow", gp=50_000, rev=150_000, jobs=2, opps=4, resp=24.0, csat=4.5)
    ranked = {s.rep_id: s for s in score_cohort([fast, slow])}
    rt = GppiKpi.LEAD_RESPONSE_TIME.value
    assert ranked["fast"].normalized[rt] > ranked["slow"].normalized[rt]


def test_score_is_bounded_and_percentile_assigned():
    reps = [_rep(f"r{i}", gp=i * 10_000, rev=i * 30_000, jobs=i + 1, opps=i + 3,
                 resp=float(i + 1), csat=4.0) for i in range(1, 6)]
    ranked = score_cohort(reps)
    for s in ranked:
        assert 0.0 <= s.score <= 100.0
    assert ranked[0].percentile == 1.0
    assert ranked[-1].percentile == 0.0


def test_single_rep_cohort_is_neutral_and_top():
    only = _rep("solo", gp=50_000, rev=150_000, jobs=2, opps=4, resp=3.0, csat=4.5)
    ranked = score_cohort([only])
    assert len(ranked) == 1
    assert ranked[0].percentile == 1.0
    # All KPIs normalize to neutral 1.0 -> score is the full 100.
    assert abs(ranked[0].score - 100.0) < 1e-6


def test_empty_cohort_returns_empty():
    assert score_cohort([]) == []


# ---------------------------------------------------------------------------
# Hierarchy
# ---------------------------------------------------------------------------

def test_adu_is_tier_one_and_bathroom_is_tier_three():
    assert tier_of("adu") == RevenueTier.TIER_1
    assert tier_of("bathroom") == RevenueTier.TIER_3
    assert tier_of("painting") == RevenueTier.TIER_4


def test_strategic_weight_decreases_with_tier():
    from backend.sales import strategic_weight
    assert strategic_weight("adu") > strategic_weight("roofing")
    assert strategic_weight("roofing") > strategic_weight("bathroom")
    assert strategic_weight("bathroom") > strategic_weight("painting")


# ---------------------------------------------------------------------------
# Lead routing (80/20 profitable-lead rule)
# ---------------------------------------------------------------------------

def test_tier_one_lead_is_always_premium():
    lead = Lead("l1", "adu", "Newburyport", 325_000)
    assert grade_lead(lead) == LeadGrade.PREMIUM


def test_qualifier_promotes_lower_tier_lead_to_premium():
    plain = Lead("l2", "roofing", "Ipswich", 40_000)
    waterfront = Lead("l3", "roofing", "Marblehead", 80_000, qualifiers=("waterfront",))
    assert profitability_score(waterfront) > profitability_score(plain)
    assert grade_lead(waterfront) == LeadGrade.PREMIUM


def test_small_painting_lead_is_standard():
    assert grade_lead(Lead("l4", "painting", "Essex", 6_000)) == LeadGrade.STANDARD


def test_premium_leads_route_to_top_performers():
    reps = [_rep(f"r{i}", gp=i * 40_000, rev=i * 120_000, jobs=i, opps=i + 2,
                 resp=float(6 - i), csat=4.0 + i * 0.1) for i in range(1, 6)]
    leaderboard = score_cohort(reps)
    leads = [
        Lead("p1", "adu", "Newburyport", 300_000),
        Lead("p2", "design_build", "Portsmouth", 400_000),
        Lead("s1", "painting", "Essex", 6_000),
    ]
    plan = route_leads(leads, leaderboard)
    top_ids = set(plan.top_performer_ids)
    premium = [r for r in plan.routed if r.grade == LeadGrade.PREMIUM]
    assert premium, "expected at least one premium lead"
    for r in premium:
        assert r.assigned_to in top_ids


def test_routing_top_performer_fraction_is_twenty_percent():
    reps = [_rep(f"r{i}", gp=i * 10_000, rev=i * 30_000, jobs=i, opps=i + 2,
                 resp=1.0, csat=4.0) for i in range(1, 11)]
    leaderboard = score_cohort(reps)
    plan = route_leads([], leaderboard)
    # 20% of 10 reps -> 2 top performers.
    assert len(plan.top_performer_ids) == 2
    assert len(plan.developing_ids) == 8


def test_routing_with_no_reps_leaves_leads_unassigned():
    plan = route_leads([Lead("l", "adu", "Rye", 300_000)], [])
    assert plan.routed[0].assigned_to is None


# ---------------------------------------------------------------------------
# Simulation + truth tagging
# ---------------------------------------------------------------------------

def test_simulation_is_deterministic():
    a = run_simulation(team_size=8, lead_count=40, seed=7)
    b = run_simulation(team_size=8, lead_count=40, seed=7)
    assert a.to_dict() == b.to_dict()


def test_simulation_is_tagged_simulated():
    sim = run_simulation(seed=1)
    assert sim.truth_tag == TruthTag.SIMULATED
    payload = sim.to_dict()
    assert payload["label"] == "SIMULATED MODEL OUTPUT"
    assert payload["needed_next"] == "ACTUAL NOBLEPORT SALES DATASET"
    assert payload["decision_authority"] == "Human Review Required"


def test_simulation_leaderboard_is_ranked():
    sim = run_simulation(team_size=8, seed=3)
    ranks = [s.rank for s in sim.leaderboard]
    assert ranks == sorted(ranks)
    scores = [s.score for s in sim.leaderboard]
    assert scores == sorted(scores, reverse=True)


def test_different_seeds_differ():
    a = run_simulation(seed=1)
    b = run_simulation(seed=2)
    assert a.to_dict() != b.to_dict()


# ---------------------------------------------------------------------------
# Data readiness gate
# ---------------------------------------------------------------------------

def test_data_readiness_transitions():
    assert run_simulation(months_of_real_data=0).readiness.mode is SimulationMode.SIMULATION_PRIMARY
    assert run_simulation(months_of_real_data=6).readiness.mode is SimulationMode.BLENDED
    assert run_simulation(months_of_real_data=12).readiness.mode is SimulationMode.DATA_PRIMARY


def test_data_readiness_weight_caps_at_one():
    assert run_simulation(months_of_real_data=24).readiness.real_data_weight == 1.0
    assert run_simulation(months_of_real_data=3).readiness.real_data_weight == 0.25


# ---------------------------------------------------------------------------
# Dashboard aggregation
# ---------------------------------------------------------------------------

def test_dashboard_aggregate_shape():
    sim = run_simulation(team_size=8, lead_count=40, seed=5)
    payload = aggregate(sim)
    assert payload["label"] == "SIMULATED MODEL OUTPUT"
    assert set(payload["headline"]) >= {"gross_profit", "revenue", "gross_margin_pct"}
    assert len(payload["markets"]) == 8
    # Premium + standard routed leads reconcile with the lead count.
    routed = payload["routing"]["premium"] + payload["routing"]["standard"]
    assert routed == 40
    assert {"lead", "sales", "financial"} <= set(payload["metric_groups"])
