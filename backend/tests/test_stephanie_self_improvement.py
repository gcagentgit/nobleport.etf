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
    ControlMode,
    Decision,
    DecisionOutcome,
    RecursiveSelfImprovementEngine,
    classify_priority,
    intake_objective,
)
from backend.agents.stephanie_policy import (
    PARAMETER_SPECS,
    LockState,
    RiskTier,
    StephaniePolicy,
)
from backend.agents.truth_registry import (
    CONTROL_RULE,
    FLYWHEELS,
    OVERALL_PLATFORM_COMPLETION,
    SUPERSEDED_COMPLETION_FIGURES,
    VOICE_LAUNCH_GATES,
    EvidenceTag,
    TruthLabel,
    label_claim,
    normalize_claim,
    reconcile,
    registry_snapshot,
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


def _lost_midmarket_leads(n: int = 10, value: float = 80_000.0) -> list[DecisionOutcome]:
    """Mid-market leads that did NOT convert — fast-tracking them wastes spend."""
    return [
        DecisionOutcome(
            lead_id=f"X{i}",
            features={"estimated_value": value, "source": "web", "property_address": None},
            converted=False,
            won_value=0.0,
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
def _low_risk_objective(_outcomes, policy: StephaniePolicy) -> float:
    """Rewards a LOW-risk parameter (lower stale_lead_days), scaled above MIN_IMPROVEMENT."""
    return -1_000.0 * policy.stale_lead_days


def test_low_risk_change_auto_applies_only_in_operational_mode():
    # OPERATIONAL_AUTO is the explicit opt-in that allows LOW-risk auto-apply.
    engine = RecursiveSelfImprovementEngine(
        objective=_low_risk_objective, control_mode=ControlMode.OPERATIONAL_AUTO,
    )
    engine.record_outcomes([DecisionOutcome(lead_id="x")])  # non-empty window
    report = engine.run_cycle(auto_apply=True)

    assert report.applied is True
    assert engine.generation == 1
    assert engine.current.stale_lead_days < StephaniePolicy().stale_lead_days


# --------------------------------------------------------------------------- #
# Control rule: fail-closed is the default; the loop only recommends
# --------------------------------------------------------------------------- #
def test_fail_closed_is_the_default():
    engine = RecursiveSelfImprovementEngine()
    assert engine.control_mode == ControlMode.FAIL_CLOSED


def test_fail_closed_blocks_low_risk_auto_apply():
    # Same LOW-risk improvement, but default FAIL_CLOSED mode must NOT deploy.
    engine = RecursiveSelfImprovementEngine(objective=_low_risk_objective)
    engine.record_outcomes([DecisionOutcome(lead_id="x")])
    report = engine.run_cycle(auto_apply=True)

    assert report.applied is False
    assert report.proposal.decision == Decision.NEEDS_HUMAN
    assert engine.generation == 0


# --------------------------------------------------------------------------- #
# Diagnose stage
# --------------------------------------------------------------------------- #
def test_proposal_carries_diagnosis_of_missed_conversions():
    engine = RecursiveSelfImprovementEngine()
    engine.record_outcomes(_converted_midmarket_leads(n=10, value=80_000.0))
    proposal = engine.propose()

    assert proposal.diagnosis is not None
    assert proposal.diagnosis.missed_conversions == 10
    assert proposal.diagnosis.value_left_on_table == 800_000.0


# --------------------------------------------------------------------------- #
# Monitor -> Lock / Rollback
# --------------------------------------------------------------------------- #
def test_applied_generation_is_provisional_until_verified():
    engine = RecursiveSelfImprovementEngine()
    engine.record_outcomes(_converted_midmarket_leads())
    engine.approve(engine.propose().id, approved_by="operator")
    assert engine.history[-1].lock_state == LockState.PROVISIONAL


def test_verify_locks_change_that_holds_up():
    engine = RecursiveSelfImprovementEngine()
    engine.record_outcomes(_converted_midmarket_leads())
    engine.approve(engine.propose().id, approved_by="operator")

    report = engine.verify()  # same window the change won on => holds
    assert report.held_up is True
    assert report.locked is True
    assert engine.history[-1].lock_state == LockState.LOCKED


def test_verify_rolls_back_change_that_regresses_on_fresh_outcomes():
    engine = RecursiveSelfImprovementEngine()
    engine.record_outcomes(_converted_midmarket_leads())
    proposal = engine.propose()
    engine.approve(proposal.id, approved_by="operator")
    lowered = engine.current.high_value_threshold
    assert lowered < 100_000.0

    # Fresh reality: those mid-market leads do NOT convert -> fast-tracking wastes spend.
    report = engine.verify(_lost_midmarket_leads())
    assert report.held_up is False
    assert report.rolled_back_to == 0
    assert engine.current.high_value_threshold == 100_000.0  # restored


def test_repeated_verification_regressions_trip_breaker():
    engine = RecursiveSelfImprovementEngine(breaker=CircuitBreaker(threshold=2))
    # Two independent provisional changes that each regress on fresh outcomes.
    for _ in range(2):
        engine.record_outcomes(_converted_midmarket_leads())
        engine.approve(engine.propose().id, approved_by="operator")
        engine.verify(_lost_midmarket_leads())
    assert engine.breaker.open is True


# --------------------------------------------------------------------------- #
# Truth registry / truth-labeling skill
# --------------------------------------------------------------------------- #
def test_truth_labeling_downgrades_unproven_live_claims():
    assert label_claim(TruthLabel.LIVE, has_evidence=False) == TruthLabel.STAGED
    assert label_claim(TruthLabel.LIVE, has_evidence=True) == TruthLabel.LIVE
    # Reconcile takes the weaker (more honest) of claimed vs observed.
    assert reconcile(TruthLabel.LIVE, TruthLabel.STAGED) == TruthLabel.STAGED
    assert reconcile(TruthLabel.STAGED, TruthLabel.LIVE) == TruthLabel.STAGED


def test_registry_snapshot_has_control_rule_and_twelve_flywheels():
    snap = registry_snapshot()
    assert snap["control_rule"] == CONTROL_RULE
    assert "not an autonomous executive signer" in CONTROL_RULE
    assert len(FLYWHEELS) == 12
    assert snap["power_center"] == "construction operations"


def test_blocked_label_reconciles_as_more_honest():
    # A STAGED claim observed as BLOCKED resolves to BLOCKED (the weaker truth).
    assert reconcile(TruthLabel.STAGED, TruthLabel.BLOCKED) == TruthLabel.BLOCKED
    assert reconcile(TruthLabel.LIVE, TruthLabel.BLOCKED) == TruthLabel.BLOCKED


def test_one_locked_completion_number():
    # Report P0 #1: exactly one figure (46%), with 48% explicitly superseded.
    snap = registry_snapshot()
    assert snap["overall_platform_completion"] == 46
    assert OVERALL_PLATFORM_COMPLETION == 46
    assert 48 in SUPERSEDED_COMPLETION_FIGURES


def test_voice_gates_zero_of_four_clear():
    snap = registry_snapshot()
    assert snap["voice_gates_total"] == 4
    assert snap["voice_gates_clear"] == 0
    assert all(g.status != "passing" for g in VOICE_LAUNCH_GATES)


def test_risky_claims_are_normalized_to_compliant_language():
    # Report P0 #3: licensing/credential claims rewritten + human-gated.
    s7 = normalize_claim("Series 7 Framework")
    assert s7 is not None
    assert "not licensed financial advice" in s7.safe
    assert s7.evidence == EvidenceTag.HUMAN_GATED

    avatar = normalize_claim("1 Billion avatar deployment")
    assert avatar.safe == "future-state avatar deployment architecture"
    assert avatar.evidence == EvidenceTag.SIMULATED

    assert normalize_claim("a perfectly fine claim") is None


def test_every_platform_module_carries_a_tier_badge():
    snap = registry_snapshot()
    tiered = {c["name"]: c["tier"] for c in snap["components"] if c["tier"]}
    assert tiered["Stephanie.ai core orchestrator"] == "LAUNCH-CRITICAL"
    assert tiered["GCagent.ai compliance monitor"] == "PHASE 2"
    assert tiered["Cyborg.ai identity layer"] == "PHASE 3"
    assert tiered["Discord Mission Control"] == "DEFERRED"


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
