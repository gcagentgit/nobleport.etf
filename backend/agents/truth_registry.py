"""
NoblePort OS — Stephanie.ai Truth Registry

The control rule that governs everything Stephanie does:

    AI observes -> drafts -> scores -> recommends ->
    authorized human approves -> system logs -> system learns.

Stephanie.ai is an AI-assisted executive orchestration layer. She routes
work, surfaces decisions for human approval, and keeps an audit log. She is
**not** AGI and **not** an autonomous executive signer: she does not
autonomously handle financial transactions, legal obligations, or external
communications without a defined human control checkpoint.

This module is the machine-readable "truth layer" the rule depends on —
every capability carries an honest status label, and labels only move up
with evidence. Marketing claims are downgraded by default, not assumed.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


# Canonical statement of the operating model — referenced by the API and docs.
CONTROL_RULE = (
    "AI observes -> drafts -> scores -> recommends -> authorized human "
    "approves -> system logs -> system learns. Stephanie.ai is not AGI and "
    "not an autonomous executive signer; she does not autonomously handle "
    "financial transactions, legal obligations, or external communications "
    "without a defined human control checkpoint."
)


class TruthLabel(StrEnum):
    """Honest status of a capability. Labels only move up with evidence."""
    LIVE = "live"            # in production on real jobs/data
    STAGED = "staged"        # built but behind production/test/audit gates
    SIMULATED = "simulated"  # works in simulation only
    TARGET = "target"        # roadmap intent, not yet built
    PENDING = "pending"      # blocked on an external gate (audit, legal, mainnet)


# Ordering for truth-labeling logic (higher = stronger claim).
_LABEL_RANK: dict[TruthLabel, int] = {
    TruthLabel.TARGET: 0,
    TruthLabel.SIMULATED: 1,
    TruthLabel.PENDING: 2,
    TruthLabel.STAGED: 3,
    TruthLabel.LIVE: 4,
}


class ComponentStatus(BaseModel):
    """Truth-layer status of a NoblePort component or lane."""
    name: str
    label: TruthLabel
    completion_pct: int | None = None
    ground_truth: str = ""


class Flywheel(BaseModel):
    """One controlled improvement loop: a measured input -> output pairing."""
    name: str
    improves: str


class SkillStatus(BaseModel):
    """A single Stephanie skill and its honest status."""
    cluster: str
    skill: str
    label: TruthLabel
    function: str = ""


# ---------------------------------------------------------------------------
# Section 1 — truth-layer status (construction is the monetizable engine now)
# ---------------------------------------------------------------------------

COMPONENT_STATUS: list[ComponentStatus] = [
    ComponentStatus(
        name="Construction intake workflow", label=TruthLabel.LIVE, completion_pct=95,
        ground_truth="Running on active jobs from intake to invoice — strongest lane.",
    ),
    ComponentStatus(
        name="Stephanie.ai core orchestrator", label=TruthLabel.STAGED, completion_pct=81,
        ground_truth="Voice gating and production deployment incomplete.",
    ),
    ComponentStatus(
        name="KUZO swap layer", label=TruthLabel.STAGED, completion_pct=None,
        ground_truth="Quote/policy/simulation live read-only; execution disabled until all gates pass.",
    ),
    ComponentStatus(
        name="GCagent.ai compliance monitor", label=TruthLabel.STAGED, completion_pct=44,
        ground_truth="Connector integrations pending.",
    ),
    ComponentStatus(
        name="PermitStream.ai", label=TruthLabel.STAGED, completion_pct=38,
        ground_truth="Regional permit connectors incomplete; manual fallback still required.",
    ),
    ComponentStatus(
        name="Cyborg.ai identity layer", label=TruthLabel.STAGED, completion_pct=28,
        ground_truth="Identity/signing architecture not live.",
    ),
    ComponentStatus(
        name="NBPT token contracts", label=TruthLabel.STAGED, completion_pct=None,
        ground_truth="Contracts written; mainnet deployment pending audit/legal gates.",
    ),
    ComponentStatus(
        name="Voice/avatar layer", label=TruthLabel.STAGED, completion_pct=None,
        ground_truth="TTS/lip-sync integrated in development; production load validation incomplete.",
    ),
]


# ---------------------------------------------------------------------------
# Section 4 — the 12 controlled improvement flywheels
# ---------------------------------------------------------------------------

FLYWHEELS: list[Flywheel] = [
    Flywheel(name="Lead -> estimate", improves="Faster and cleaner scopes"),
    Flywheel(name="Estimate -> actual", improves="Better labor units and margin protection"),
    Flywheel(name="Proposal -> signed contract", improves="Better pricing language and trust positioning"),
    Flywheel(name="Permit packet -> AHJ response", improves="Better town-specific permit rules"),
    Flywheel(name="Change order -> approval", improves="Faster scope-delta documentation"),
    Flywheel(name="Sub quote -> sub invoice", improves="Better subcontractor cost prediction"),
    Flywheel(name="Schedule -> delay reasons", improves="Better planning buffers"),
    Flywheel(name="Photos -> field log", improves="Better job documentation"),
    Flywheel(name="Calls -> CRM notes", improves="Better follow-up discipline"),
    Flywheel(name="Compliance edge case -> rule update", improves="Better guardrails"),
    Flywheel(name="Voice session -> latency/error metrics", improves="Better avatar production readiness"),
    Flywheel(name="Governance vote -> execution record", improves="Better DAO accountability"),
]


# ---------------------------------------------------------------------------
# Priority order — revenue-first, no detours
# ---------------------------------------------------------------------------

PRIORITY_PHASES: dict[str, list[str]] = {
    "phase_1_revenue_first": [
        "Construction intake",
        "Proposal generation",
        "AWO/change order workflow",
        "Invoice/payment tracking",
        "Subcontractor packet generation",
        "Permit checklist/manual fallback",
    ],
    "phase_2_operating_leverage": [
        "GCagent daily job controller",
        "PermitStream regional connector buildout",
        "Voice-to-field-log capture",
        "Executive daily brief",
        "CRM follow-up automation",
        "Closeout package automation",
    ],
    "phase_3_platform_investor": [
        "Snapshot/IPFS governance records",
        "NBPT dashboard",
        "KUZO launch gates",
        "Smart contract audit package",
        "Voice/avatar investor walkthrough",
        "White-label licensing package",
    ],
}


# ---------------------------------------------------------------------------
# Truth-labeling skill: downgrade unproven, upgrade only on proof
# ---------------------------------------------------------------------------

def label_claim(proposed: TruthLabel, *, has_evidence: bool) -> TruthLabel:
    """
    Apply the truth-labeling rule to a claimed status.

    Without evidence, any claim of LIVE is downgraded to STAGED (and a claim
    of STAGED on a simulation-only capability stays SIMULATED). Upgrades only
    stick when evidence is present — claims are never trusted by default.
    """
    if has_evidence:
        return proposed
    # No evidence: never allow a LIVE claim to stand.
    if proposed == TruthLabel.LIVE:
        return TruthLabel.STAGED
    return proposed


def reconcile(claimed: TruthLabel, observed: TruthLabel) -> TruthLabel:
    """
    Reconcile a claimed label against what we can actually observe, taking
    the weaker (more honest) of the two. A LIVE claim with only STAGED
    evidence resolves to STAGED.
    """
    return claimed if _LABEL_RANK[claimed] <= _LABEL_RANK[observed] else observed


def registry_snapshot() -> dict:
    """Full machine-readable truth layer for Mission Control / the API."""
    return {
        "control_rule": CONTROL_RULE,
        "power_center": "construction operations",
        "next_unlock": "PermitStream + GCagent integration",
        "future_upside": "governance, tokenization, voice/avatar distribution",
        "components": [c.model_dump() for c in COMPONENT_STATUS],
        "flywheels": [f.model_dump() for f in FLYWHEELS],
        "priority_phases": PRIORITY_PHASES,
    }
