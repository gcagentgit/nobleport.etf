"""
Stephanie.ai recursive self-improvement — unit tests.

Pure-Python (no DB, no network). Exercises the bounded improvement loop:
counterfactual scoring, governance gating, circuit breaker, generations,
and rollback.
"""

from __future__ import annotations

from backend.agents.self_improvement import (
    DEFAULT_FAST_TRACK_COST,
    CircuitBreaker,
    Decision,
    DecisionOutcome,
    RecursiveSelfImprovementEngine,
    classify_priority,
    intake_objective,
)
from backend.agents.stephanie_policy import (
    PARAMETER_SPECS,
    RiskTier,
    StephaniePolicy,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _converted_midmarket_leads(n: int = 10, value: float = 80_000.0) -> list[DecisionOutcome]:
    """Leads that converted at a value BELOW the default 100k fast-track cutoff.

    With the default threshold these convert without being prioritized (money
    left on the table); lowering the threshold should capture them.
    """
    return [
        DecisionOutcome(
            lead_id=f"L{i}",
            features={"estimated_value": value, "source": "web", "property_address": None},
            converted=True,
            won_value=value,
        )
        for i in range(n)
    ]


# --------------------------------------------------------------------------- #
# Policy defaults preserve original behavior
# --------------------------------------------------------------------------- #
def test_defaults_match_shipped_values():
    p = StephaniePolicy()
    assert p.high_value_threshold == 100_000.0
    assert p.stale_lead_days == 5.0
    assert p.stale_critical_days == 14.0
    assert p.health_weight_critical == 15.0


def test_classify_priority_matches_route_intake_logic():
    p = StephaniePolicy()
    assert classify_priority({"estimated_value": 120_000}, p) == "high"
    assert classify_priority({"estimated_value": 80_000, "source": "referral"}, p) == "high"
    assert classify_priority({"estimated_value": 80_000, "property_address": "1 Main St"}, p) == "medium"
    assert classify_priority({"estimated_value": 80_000, "source": "web"}, p) == "normal"


# --------------------------------------------------------------------------- #
# Bounds & step limits
# --------------------------------------------------------------------------- #
def test_parameter_clamp_and_step_limit():
    spec = PARAMETER_SPECS["high_value_threshold"]
    assert spec.clamp(10_000) == spec.minimum
    assert spec.clamp(999_999) == spec.maximum
    # A jump larger than max_step is capped to max_step.
    stepped = spec.limit_step(100_000, 100_000 - 80_000)
    assert stepped == 100_000 - spec.max_step


def test_with_changes_clamps_out_of_range_values():
    p = StephaniePolicy().with_changes({"high_value_threshold": 5_000})
    assert p.high_value_threshold == PARAMETER_SPECS["high_value_threshold"].minimum


# --------------------------------------------------------------------------- #
# Counterfactual objective rewards capturing converted mid-market leads
# --------------------------------------------------------------------------- #
def test_objective_improves_when_threshold_lowered_to_capture_conversions():
    outcomes = _converted_midmarket_leads()
    baseline = intake_objective(outcomes, StephaniePolicy())
    lowered = intake_objective(outcomes, StephaniePolicy().with_changes({"high_value_threshold": 75_000}))
    assert lowered > baseline


# --------------------------------------------------------------------------- #
# Proposal generation is bounded and governed
# --------------------------------------------------------------------------- #
def test_propose_picks_bounded_high_risk_change_and_requires_human():
    engine = RecursiveSelfImprovementEngine()
    engine.record_outcomes(_converted_midmarket_leads())
    proposal = engine.propose()

    assert proposal is not None
    # Only parameter affecting the intake objective is the HIGH-risk threshold.
    assert "high_value_threshold" in proposal.changes
    # Bounded: moved exactly one max_step, not an uncontrolled jump.
    spec = PARAMETER_SPECS["high_value_threshold"]
    assert proposal.changes["high_value_threshold"] == 100_000 - spec.max_step
    assert proposal.improvement > 0
    # HIGH risk => never auto-applied.
    assert proposal.risk_tier == RiskTier.HIGH
    assert proposal.decision == Decision.NEEDS_HUMAN


def test_run_cycle_dry_run_does_not_apply_high_risk():
    engine = RecursiveSelfImprovementEngine()
    engine.record_outcomes(_converted_midmarket_leads())
    report = engine.run_cycle(auto_apply=True)  # auto_apply set, but change is HIGH risk
    assert report.proposal is not None
    assert report.applied is False
    assert engine.generation == 0


# --------------------------------------------------------------------------- #
# LOW-risk change with a custom objective auto-applies
# --------------------------------------------------------------------------- #
def test_low_risk_change_auto_applies():
    # Objective rewards a LOW-risk parameter (lower stale_lead_days), scaled
    # above MIN_IMPROVEMENT so the move qualifies.
    def obj(_outcomes, policy: StephaniePolicy) -> float:
        return -1_000.0 * policy.stale_lead_days

    engine = RecursiveSelfImprovementEngine(objective=obj)
    engine.record_outcomes([DecisionOutcome(lead_id="x")])  # non-empty window
    report = engine.run_cycle(auto_apply=True)

    assert report.applied is True
    assert engine.generation == 1
    assert engine.current.stale_lead_days < StephaniePolicy().stale_lead_days


# --------------------------------------------------------------------------- #
# Generations, approval, and rollback
# --------------------------------------------------------------------------- #
def test_approve_increments_generation_and_links_parent():
    engine = RecursiveSelfImprovementEngine()
    engine.record_outcomes(_converted_midmarket_leads())
    proposal = engine.propose()
    version = engine.approve(proposal.id, approved_by="operator")

    assert engine.generation == 1
    assert version.parent_generation == 0
    assert version.generation == 1
    assert proposal.id not in engine.pending


def test_rollback_restores_prior_generation():
    engine = RecursiveSelfImprovementEngine()
    engine.record_outcomes(_converted_midmarket_leads())
    original = engine.current.high_value_threshold

    engine.approve(engine.propose().id, approved_by="operator")
    assert engine.current.high_value_threshold != original

    engine.rollback(0, actor="operator")
    assert engine.current.high_value_threshold == original
    # Rollback is recorded as a new generation, not a deletion.
    assert engine.generation == 2


# --------------------------------------------------------------------------- #
# Circuit breaker halts the loop
# --------------------------------------------------------------------------- #
def test_circuit_breaker_trips_after_consecutive_regressions():
    breaker = CircuitBreaker(threshold=2)
    breaker.record(improved=False)
    assert breaker.open is False
    breaker.record(improved=False)
    assert breaker.open is True


def test_open_breaker_blocks_cycle():
    engine = RecursiveSelfImprovementEngine()
    engine.record_outcomes(_converted_midmarket_leads())
    engine.breaker.open = True
    report = engine.run_cycle(auto_apply=True)
    assert report.breaker_open is True
    assert report.proposal is None
    assert engine.generation == 0


def test_breaker_reset_reenables_loop():
    engine = RecursiveSelfImprovementEngine()
    engine.breaker.open = True
    engine.breaker.reset()
    assert engine.breaker.open is False
    assert engine.breaker.consecutive_regressions == 0
