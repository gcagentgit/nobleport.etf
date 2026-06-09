"""
NoblePort OS — Stephanie.ai Tunable Policy

Stephanie's decision-making used to live as hardcoded literals scattered
through her routing and ops-brief logic (``estimated_value >= 100_000``,
``days_stale > 14``, severity weights, ...). To make her *self-improving*
those literals are lifted into a single versioned, bounded policy object.

The recursive self-improvement loop (``backend.agents.self_improvement``)
proposes adjustments to these parameters, proves they improve a defined
objective on historical outcomes, and applies them through governance.

Two invariants keep this safe:

  1. Every tunable parameter has hard ``min``/``max`` bounds and a
     ``max_step`` (the most it may move in a single generation). The loop
     physically cannot drive a parameter out of its safe range or make a
     large uncontrolled jump.
  2. Every parameter carries a ``risk_tier``. LOW-tier changes may be
     auto-applied when improvement is proven; HIGH-tier changes always
     require human approval — mirroring Cyborg's HUMAN_REQUIRED_ACTIONS.

Defaults below are exactly the values Stephanie shipped with, so adopting
the policy changes no behavior until the loop tunes it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class RiskTier(StrEnum):
    """How much human oversight a parameter change requires."""
    LOW = "low"        # auto-apply when improvement is proven
    MEDIUM = "medium"  # auto-apply only with strong improvement + high confidence
    HIGH = "high"      # always requires human approval


class LockState(StrEnum):
    """
    Lifecycle of an applied policy generation under the Monitor → Lock /
    Rollback stage of the controlled loop.
    """
    LOCKED = "locked"          # proven / baseline — the stable in-force policy
    PROVISIONAL = "provisional"  # applied, but not yet proven on fresh outcomes
    ROLLED_BACK = "rolled_back"  # superseded by a rollback after it regressed


class ParameterSpec(BaseModel):
    """Safe-range definition for a single tunable parameter."""
    name: str
    minimum: float
    maximum: float
    max_step: float = Field(
        ...,
        description="Largest absolute change permitted in one generation.",
    )
    risk_tier: RiskTier = RiskTier.LOW
    description: str = ""

    def clamp(self, value: float) -> float:
        """Clamp a value into the parameter's hard bounds."""
        return max(self.minimum, min(self.maximum, value))

    def limit_step(self, current: float, proposed: float) -> float:
        """Limit a proposed move to at most ``max_step`` from ``current``."""
        delta = proposed - current
        if abs(delta) > self.max_step:
            delta = self.max_step if delta > 0 else -self.max_step
        return self.clamp(current + delta)


class StephaniePolicy(BaseModel):
    """
    The full set of parameters that govern Stephanie's decisions.

    Field defaults equal the original hardcoded values, so behavior is
    unchanged until the self-improvement loop tunes them.
    """

    # -- Intake routing ------------------------------------------------------
    high_value_threshold: float = Field(
        default=100_000.0,
        description="Leads at/above this estimated value are fast-tracked "
        "(senior estimator + 48h site visit). HIGH risk: drives resource spend.",
    )

    # -- Ops-brief: stale leads ---------------------------------------------
    stale_lead_days: float = Field(
        default=5.0,
        description="A lead untouched for this many days is surfaced as stale.",
    )
    stale_critical_days: float = Field(
        default=14.0,
        description="Stale beyond this many days => critical severity.",
    )
    stale_high_days: float = Field(
        default=7.0,
        description="Stale beyond this many days => high severity.",
    )

    # -- Ops-brief: deposits & margin ---------------------------------------
    deposit_critical_outstanding: float = Field(
        default=10_000.0,
        description="Outstanding deposit above this => critical severity.",
    )
    at_risk_margin_floor_pct: float = Field(
        default=15.0,
        description="Job margin below this percent is flagged at-risk. "
        "MEDIUM risk: affects which jobs draw management attention.",
    )
    at_risk_critical_margin_pct: float = Field(
        default=5.0,
        description="Job margin below this percent => critical severity.",
    )

    # -- Ops-brief: health score weights ------------------------------------
    health_weight_critical: float = Field(
        default=15.0,
        description="Health-score penalty per critical action item.",
    )
    health_weight_high: float = Field(
        default=5.0,
        description="Health-score penalty per high-severity action item.",
    )
    health_weight_medium: float = Field(
        default=2.0,
        description="Health-score penalty per medium-severity action item.",
    )

    def tunables(self) -> dict[str, float]:
        """Return the tunable parameters as a flat name -> value mapping."""
        return {name: float(getattr(self, name)) for name in PARAMETER_SPECS}

    def with_changes(self, changes: dict[str, float]) -> "StephaniePolicy":
        """Return a copy with ``changes`` applied, each clamped to its bounds."""
        data = self.model_dump()
        for name, value in changes.items():
            spec = PARAMETER_SPECS.get(name)
            data[name] = spec.clamp(value) if spec else value
        return StephaniePolicy(**data)


# ---------------------------------------------------------------------------
# Safe-range registry — the loop may only tune parameters listed here.
# ---------------------------------------------------------------------------

PARAMETER_SPECS: dict[str, ParameterSpec] = {
    spec.name: spec
    for spec in [
        ParameterSpec(
            name="high_value_threshold",
            minimum=40_000.0, maximum=250_000.0, max_step=25_000.0,
            risk_tier=RiskTier.HIGH,
            description="Fast-track value cutoff (drives senior-estimator spend).",
        ),
        ParameterSpec(
            name="stale_lead_days",
            minimum=2.0, maximum=14.0, max_step=2.0,
            risk_tier=RiskTier.LOW,
            description="Days untouched before a lead is surfaced as stale.",
        ),
        ParameterSpec(
            name="stale_critical_days",
            minimum=7.0, maximum=30.0, max_step=3.0,
            risk_tier=RiskTier.LOW,
        ),
        ParameterSpec(
            name="stale_high_days",
            minimum=3.0, maximum=14.0, max_step=2.0,
            risk_tier=RiskTier.LOW,
        ),
        ParameterSpec(
            name="deposit_critical_outstanding",
            minimum=2_500.0, maximum=50_000.0, max_step=2_500.0,
            risk_tier=RiskTier.LOW,
        ),
        ParameterSpec(
            name="at_risk_margin_floor_pct",
            minimum=5.0, maximum=30.0, max_step=3.0,
            risk_tier=RiskTier.MEDIUM,
            description="Margin floor below which a job is flagged at-risk.",
        ),
        ParameterSpec(
            name="at_risk_critical_margin_pct",
            minimum=0.0, maximum=15.0, max_step=2.0,
            risk_tier=RiskTier.LOW,
        ),
        ParameterSpec(
            name="health_weight_critical",
            minimum=5.0, maximum=30.0, max_step=3.0,
            risk_tier=RiskTier.LOW,
        ),
        ParameterSpec(
            name="health_weight_high",
            minimum=1.0, maximum=15.0, max_step=2.0,
            risk_tier=RiskTier.LOW,
        ),
        ParameterSpec(
            name="health_weight_medium",
            minimum=0.0, maximum=8.0, max_step=1.0,
            risk_tier=RiskTier.LOW,
        ),
    ]
}


class PolicyVersion(BaseModel):
    """
    An applied generation of Stephanie's policy.

    ``parent_generation`` links each generation to the one it improved on,
    making the improvement history an explicit recursive chain.
    """
    generation: int
    parent_generation: int | None
    policy: StephaniePolicy
    objective_score: float
    lock_state: LockState = LockState.PROVISIONAL
    rationale: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
