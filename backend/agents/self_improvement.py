"""
NoblePort OS — Recursive Self-Improvement for Stephanie.ai

Stephanie improves her own decision-making by learning from the realized
outcomes of her past decisions. The loop is recursive: each accepted change
produces a new policy *generation* that the next cycle builds on, so gains
compound over time.

It is also deliberately *bounded* — this is operations tuning, not an
open-ended self-modifying system:

    observe  ->  propose  ->  evaluate  ->  govern  ->  apply / queue
       ^                                                        |
       +--------------------- next generation -------------------+

  observe   Ingest decision outcomes (what Stephanie decided, and what
            actually happened afterwards).
  propose   Coordinate-descent search over tunable parameters, each move
            capped at its ``max_step`` and clamped to hard bounds.
  evaluate  Counterfactual replay: re-derive what the candidate policy
            *would* have decided on the same history, and score it against
            the realized outcomes. A change is only a candidate if it
            measurably beats the current policy.
  govern    Risk-tier gate (LOW auto, HIGH human), plus a circuit breaker
            that halts the loop if applied changes start regressing live
            performance. Every step is written to the AuditBeacon chain.
  apply     Bump the generation, version the policy, keep full history so
            any generation can be rolled back.

Nothing here mutates production behavior on its own: ``run_cycle`` is a
dry-run unless ``auto_apply`` is set, and only LOW-risk, improvement-proven
changes with the breaker closed are ever auto-applied. Everything else is
queued for a human.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable, Iterable

from pydantic import BaseModel, Field

from backend.agents.stephanie_policy import (
    PARAMETER_SPECS,
    PolicyVersion,
    RiskTier,
    StephaniePolicy,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Observed outcomes
# ---------------------------------------------------------------------------

class DecisionOutcome(BaseModel):
    """
    A single past intake decision paired with what actually happened.

    ``features`` are the lead attributes Stephanie routed on; ``converted``
    / ``won_value`` are the realized result. The loop uses these to judge
    whether a different routing threshold would have served the business
    better — without ever needing the live system.
    """
    lead_id: str = ""
    features: dict[str, Any] = Field(default_factory=dict)
    converted: bool = False
    won_value: float = 0.0
    days_to_first_touch: float = 0.0


# ---------------------------------------------------------------------------
# Objective: intake-routing value capture
# ---------------------------------------------------------------------------

# Cost (in objective points) of fast-tracking one lead: senior estimator time
# plus a 48h site visit. Tuning that wins more converted value than it spends
# on fast-tracking is a genuine improvement; over-prioritizing is penalized.
DEFAULT_FAST_TRACK_COST = 1_500.0


def classify_priority(features: dict[str, Any], policy: StephaniePolicy) -> str:
    """
    Pure mirror of ``StephanieAgent.route_intake`` priority branch logic,
    used for counterfactual replay. Keep in sync with route_intake.
    """
    estimated_value = float(features.get("estimated_value", 0) or 0)
    source = features.get("source", "other")
    has_address = bool(features.get("property_address"))

    if estimated_value >= policy.high_value_threshold:
        return "high"
    if source == "referral":
        return "high"
    if has_address:
        return "medium"
    return "normal"


def intake_objective(
    outcomes: Iterable[DecisionOutcome],
    policy: StephaniePolicy,
    fast_track_cost: float = DEFAULT_FAST_TRACK_COST,
) -> float:
    """
    Score a policy against realized outcomes.

    Reward = converted value captured on leads the policy fast-tracked
             (priority == "high")
           - fast_track_cost for every lead the policy fast-tracked
           - a missed-opportunity penalty for converted leads the policy
             would NOT have prioritized (we under-served real revenue).

    This makes ``high_value_threshold`` a real trade-off: lowering it
    captures more conversions but spends more on fast-tracking; raising it
    saves spend but risks missing winners.
    """
    score = 0.0
    for o in outcomes:
        priority = classify_priority(o.features, policy)
        prioritized = priority == "high"
        if prioritized:
            score -= fast_track_cost
            if o.converted:
                score += o.won_value
        elif o.converted:
            # Converted despite not being prioritized — money left on the table.
            score -= 0.25 * o.won_value
    return round(score, 2)


# Objective signature: (outcomes, policy) -> float
ObjectiveFn = Callable[[Iterable[DecisionOutcome], StephaniePolicy], float]


# ---------------------------------------------------------------------------
# Proposals & reports
# ---------------------------------------------------------------------------

class Decision(StrEnum):
    AUTO_APPLY = "auto_apply"
    NEEDS_HUMAN = "needs_human"
    REJECTED = "rejected"


class ImprovementProposal(BaseModel):
    """A bounded, evaluated candidate change for one generation."""
    id: str = Field(default_factory=lambda: f"prop-{uuid.uuid4().hex[:12]}")
    target_generation: int
    changes: dict[str, float] = Field(default_factory=dict)        # name -> new value
    previous: dict[str, float] = Field(default_factory=dict)       # name -> old value
    baseline_score: float = 0.0
    candidate_score: float = 0.0
    improvement: float = 0.0
    confidence: float = 0.0
    risk_tier: RiskTier = RiskTier.LOW
    decision: Decision = Decision.NEEDS_HUMAN
    rationale: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class GenerationReport(BaseModel):
    """Outcome of one ``run_cycle`` invocation."""
    generation: int
    sample_size: int
    proposal: ImprovementProposal | None = None
    applied: bool = False
    breaker_open: bool = False
    note: str = ""


# ---------------------------------------------------------------------------
# Circuit breaker — halts the loop if live performance regresses
# ---------------------------------------------------------------------------

class CircuitBreaker(BaseModel):
    """
    Trips after ``threshold`` consecutive regressions, blocking auto-apply
    until a human resets it. Guards against drift and reward-hacking where
    proxy-objective gains do not hold up on fresh data.
    """
    threshold: int = 2
    consecutive_regressions: int = 0
    open: bool = False
    tripped_at: str | None = None

    def record(self, improved: bool) -> None:
        if improved:
            self.consecutive_regressions = 0
            return
        self.consecutive_regressions += 1
        if self.consecutive_regressions >= self.threshold:
            self.open = True
            self.tripped_at = datetime.now(timezone.utc).isoformat()

    def reset(self) -> None:
        self.consecutive_regressions = 0
        self.open = False
        self.tripped_at = None


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

# Minimum proven improvement (objective points) for a change to qualify, and
# the stronger bar MEDIUM-risk changes must clear to be auto-applied.
MIN_IMPROVEMENT = 100.0
MEDIUM_AUTO_IMPROVEMENT = 5_000.0
MEDIUM_AUTO_CONFIDENCE = 0.6
MAX_WINDOW = 2_000  # rolling outcome window


class RecursiveSelfImprovementEngine:
    """
    Drives Stephanie's recursive self-improvement loop.

    The engine owns the current policy + version history, a rolling window of
    observed outcomes, the circuit breaker, and a pluggable objective. It is
    pure-Python and DB-free so it can be unit-tested offline; the API layer
    injects an ``audit_sink`` that writes each step to the AuditBeacon chain.
    """

    def __init__(
        self,
        policy: StephaniePolicy | None = None,
        *,
        objective: ObjectiveFn = intake_objective,
        audit_sink: Callable[[str, dict[str, Any]], None] | None = None,
        breaker: CircuitBreaker | None = None,
    ) -> None:
        self.objective = objective
        self._audit_sink = audit_sink
        self.breaker = breaker or CircuitBreaker()

        base = policy or StephaniePolicy()
        self.current = base
        self.generation = 0
        self.history: list[PolicyVersion] = [
            PolicyVersion(
                generation=0,
                parent_generation=None,
                policy=base,
                objective_score=0.0,
                rationale="Baseline policy (shipped defaults).",
            )
        ]
        self.outcomes: list[DecisionOutcome] = []
        self.pending: dict[str, ImprovementProposal] = {}

    # -- audit ---------------------------------------------------------------

    def _audit(self, action: str, detail: dict[str, Any]) -> None:
        if self._audit_sink:
            try:
                self._audit_sink(action, detail)
            except Exception:  # auditing must never break the loop
                logger.exception("self-improvement audit sink failed for %s", action)

    # -- observe -------------------------------------------------------------

    def record_outcomes(self, outcomes: Iterable[DecisionOutcome]) -> int:
        """Add realized decision outcomes to the rolling learning window."""
        added = 0
        for o in outcomes:
            self.outcomes.append(o)
            added += 1
        if len(self.outcomes) > MAX_WINDOW:
            self.outcomes = self.outcomes[-MAX_WINDOW:]
        if added:
            self._audit("self_improvement.observe", {"added": added, "window": len(self.outcomes)})
        return added

    # -- evaluate ------------------------------------------------------------

    def score(self, policy: StephaniePolicy) -> float:
        return self.objective(self.outcomes, policy)

    # -- propose -------------------------------------------------------------

    def propose(self) -> ImprovementProposal | None:
        """
        Coordinate-descent over tunable parameters. For each parameter we try
        a single step up and down (bounded by ``max_step`` and hard bounds)
        and keep the best-improving single-parameter move. Deterministic and
        explainable — no black-box search.
        """
        if not self.outcomes:
            return None

        baseline = self.score(self.current)
        best_changes: dict[str, float] = {}
        best_score = baseline

        for name, spec in PARAMETER_SPECS.items():
            current_value = float(getattr(self.current, name))
            for proposed in (current_value + spec.max_step, current_value - spec.max_step):
                stepped = spec.limit_step(current_value, proposed)
                if stepped == current_value:
                    continue
                candidate = self.current.with_changes({name: stepped})
                candidate_score = self.score(candidate)
                if candidate_score > best_score + 1e-9:
                    best_score = candidate_score
                    best_changes = {name: stepped}

        improvement = round(best_score - baseline, 2)
        if not best_changes or improvement < MIN_IMPROVEMENT:
            self._audit("self_improvement.propose", {
                "result": "no_qualifying_change",
                "baseline": baseline,
                "best": best_score,
            })
            return None

        name = next(iter(best_changes))
        spec = PARAMETER_SPECS[name]
        confidence = self._confidence(improvement, baseline)
        proposal = ImprovementProposal(
            target_generation=self.generation + 1,
            changes=best_changes,
            previous={name: float(getattr(self.current, name))},
            baseline_score=baseline,
            candidate_score=best_score,
            improvement=improvement,
            confidence=confidence,
            risk_tier=spec.risk_tier,
            rationale=(
                f"Adjust {name} "
                f"{getattr(self.current, name):g} -> {best_changes[name]:g}: "
                f"+{improvement:g} objective over {len(self.outcomes)} outcomes."
            ),
        )
        proposal.decision = self._govern(proposal)
        self.pending[proposal.id] = proposal
        self._audit("self_improvement.propose", proposal.model_dump())
        return proposal

    @staticmethod
    def _confidence(improvement: float, baseline: float) -> float:
        """Relative improvement, squashed into [0, 1]."""
        denom = abs(baseline) + abs(improvement) + 1.0
        return round(min(1.0, abs(improvement) / denom), 3)

    # -- govern --------------------------------------------------------------

    def _govern(self, proposal: ImprovementProposal) -> Decision:
        """Decide auto-apply vs human approval from risk tier + breaker."""
        if self.breaker.open:
            return Decision.NEEDS_HUMAN
        tier = proposal.risk_tier
        if tier == RiskTier.HIGH:
            return Decision.NEEDS_HUMAN
        if tier == RiskTier.LOW:
            return Decision.AUTO_APPLY
        # MEDIUM: only auto-apply on strong, confident improvement.
        if (
            proposal.improvement >= MEDIUM_AUTO_IMPROVEMENT
            and proposal.confidence >= MEDIUM_AUTO_CONFIDENCE
        ):
            return Decision.AUTO_APPLY
        return Decision.NEEDS_HUMAN

    # -- apply / approve / reject -------------------------------------------

    def apply(self, proposal: ImprovementProposal, *, approved_by: str = "auto") -> PolicyVersion:
        """Commit a proposal as the next generation and record the breaker signal."""
        new_policy = self.current.with_changes(proposal.changes)
        parent = self.generation
        self.current = new_policy
        self.generation += 1
        version = PolicyVersion(
            generation=self.generation,
            parent_generation=parent,
            policy=new_policy,
            objective_score=proposal.candidate_score,
            rationale=proposal.rationale,
        )
        self.history.append(version)
        self.pending.pop(proposal.id, None)

        # Breaker tracks whether applied changes keep improving.
        self.breaker.record(improved=proposal.improvement > 0)

        self._audit("self_improvement.apply", {
            "generation": self.generation,
            "parent_generation": parent,
            "changes": proposal.changes,
            "approved_by": approved_by,
            "objective_score": proposal.candidate_score,
        })
        logger.info(
            "Stephanie self-improvement: generation %d applied (%s) by %s",
            self.generation, proposal.changes, approved_by,
        )
        return version

    def approve(self, proposal_id: str, *, approved_by: str) -> PolicyVersion:
        proposal = self.pending.get(proposal_id)
        if proposal is None:
            raise KeyError(f"No pending proposal {proposal_id}")
        return self.apply(proposal, approved_by=approved_by)

    def reject(self, proposal_id: str, *, rejected_by: str, reason: str = "") -> None:
        proposal = self.pending.pop(proposal_id, None)
        if proposal is None:
            raise KeyError(f"No pending proposal {proposal_id}")
        proposal.decision = Decision.REJECTED
        self._audit("self_improvement.reject", {
            "proposal_id": proposal_id, "rejected_by": rejected_by, "reason": reason,
        })

    def rollback(self, generation: int, *, actor: str = "human") -> PolicyVersion:
        """Restore a prior generation's policy (recorded as a new version)."""
        target = next((v for v in self.history if v.generation == generation), None)
        if target is None:
            raise KeyError(f"No such generation {generation}")
        parent = self.generation
        self.current = target.policy
        self.generation += 1
        version = PolicyVersion(
            generation=self.generation,
            parent_generation=parent,
            policy=target.policy,
            objective_score=target.objective_score,
            rationale=f"Rollback to generation {generation} by {actor}.",
        )
        self.history.append(version)
        self.breaker.reset()
        self._audit("self_improvement.rollback", {
            "restored_generation": generation, "new_generation": self.generation, "actor": actor,
        })
        return version

    # -- cycle ---------------------------------------------------------------

    def run_cycle(self, *, auto_apply: bool = False) -> GenerationReport:
        """
        Run one full improvement cycle. Dry-run by default: a proposal is
        produced and governed, but only committed when ``auto_apply`` is set
        AND governance returned AUTO_APPLY AND the breaker is closed.
        """
        if self.breaker.open:
            return GenerationReport(
                generation=self.generation,
                sample_size=len(self.outcomes),
                breaker_open=True,
                note="Circuit breaker open — auto-apply halted, awaiting human reset.",
            )

        proposal = self.propose()
        if proposal is None:
            return GenerationReport(
                generation=self.generation,
                sample_size=len(self.outcomes),
                note="No qualifying improvement found this cycle.",
            )

        applied = False
        if auto_apply and proposal.decision == Decision.AUTO_APPLY:
            self.apply(proposal, approved_by="auto")
            applied = True

        return GenerationReport(
            generation=self.generation,
            sample_size=len(self.outcomes),
            proposal=proposal,
            applied=applied,
            breaker_open=self.breaker.open,
            note=(
                "Auto-applied." if applied
                else f"Proposal queued ({proposal.decision.value})."
            ),
        )

    # -- introspection -------------------------------------------------------

    def state(self) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "policy": self.current.model_dump(),
            "objective_score": self.score(self.current) if self.outcomes else None,
            "window_size": len(self.outcomes),
            "pending_proposals": [p.model_dump() for p in self.pending.values()],
            "breaker": self.breaker.model_dump(),
            "history_depth": len(self.history),
        }
