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
    """
    Operational/deployment state of a capability. Labels only move up with
    evidence. Vocabulary aligned with the Notion Command Center truth layer.
    """
    LIVE = "live"            # in production on real jobs/data
    STAGED = "staged"        # built/demoable but not production-proven
    SIMULATED = "simulated"  # works on sample/demo data only
    BLOCKED = "blocked"      # waiting on an upstream dependency / failing gate
    TARGET = "target"        # roadmap intent, not yet built
    PENDING = "pending"      # blocked on an external gate (audit, legal, mainnet)


# Ordering for truth-labeling logic (higher = stronger claim). BLOCKED ranks
# low: an active blocker is one of the most honest "not done" signals.
_LABEL_RANK: dict[TruthLabel, int] = {
    TruthLabel.TARGET: 0,
    TruthLabel.BLOCKED: 1,
    TruthLabel.SIMULATED: 2,
    TruthLabel.PENDING: 3,
    TruthLabel.STAGED: 4,
    TruthLabel.LIVE: 5,
}


class EvidenceTag(StrEnum):
    """
    Credibility of a *number or claim*, orthogonal to deployment state. This is
    the discipline the optimization report demands: a polished dashboard must
    not render management estimates, technical claims, and future-state in the
    same visual language. Every datum carries one of these.
    """
    VERIFIED = "verified"        # evidence exists (export, log, third party)
    MGMT_EST = "mgmt_est"        # management estimate only
    SIMULATED = "simulated"      # sample/demo data
    BLOCKED = "blocked"          # waiting on upstream dependency
    HUMAN_GATED = "human_gated"  # cannot execute without Michael/licensed approval


class ComponentStatus(BaseModel):
    """Truth-layer status of a NoblePort component or lane."""
    name: str
    label: TruthLabel
    completion_pct: int | None = None
    tier: str | None = None
    # Default MGMT_EST: per the optimization report, the whole status picture
    # is a management estimate until receipts (exports, CPA review) exist.
    evidence: EvidenceTag = EvidenceTag.MGMT_EST
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
        tier="LAUNCH-CRITICAL",
        ground_truth="Closest to a usable demo state; voice gates 0/4 — NOT launch-ready. Demo must be labelled STAGED.",
    ),
    ComponentStatus(
        name="KUZO swap layer", label=TruthLabel.STAGED, completion_pct=None,
        ground_truth="Quote/policy/simulation live read-only; execution disabled until all gates pass.",
    ),
    ComponentStatus(
        name="GCagent.ai compliance monitor", label=TruthLabel.STAGED, completion_pct=44,
        tier="PHASE 2",
        ground_truth="Solid Phase 2 base; ERPNext integration only ~10%.",
    ),
    ComponentStatus(
        name="PermitStream.ai", label=TruthLabel.STAGED, completion_pct=38,
        tier="PHASE 2",
        ground_truth="Workflow direction is right; municipal connectors are the weak point.",
    ),
    ComponentStatus(
        name="Cyborg.ai identity layer", label=TruthLabel.STAGED, completion_pct=28,
        tier="PHASE 3",
        ground_truth="Web3 layer staged; HSM signing (~10%) is the major blocker.",
    ),
    ComponentStatus(
        name="Discord Mission Control", label=TruthLabel.TARGET, completion_pct=8,
        tier="DEFERRED",
        ground_truth="Properly deferred — do not spend cycles here yet.",
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
# Locked headline numbers (optimization report P0 #1: ONE completion number)
# ---------------------------------------------------------------------------

# The dashboard showed both 48% (header chip) and 46% (platform section).
# 46% is the locked figure; 48% is superseded to remove the conflict.
OVERALL_PLATFORM_COMPLETION = 46
SUPERSEDED_COMPLETION_FIGURES = [48]
PLATFORM_ARR = 0  # pre-revenue / staged — never frame as traction
PLATFORM_NARRATIVE = "pre-Series A preparation / strategic seed narrative"


class Gate(BaseModel):
    """A pass/fail launch or readiness gate with its evidence state."""
    name: str
    target: str
    current: str
    status: str  # failing | in_progress | pending | passing
    evidence: EvidenceTag = EvidenceTag.MGMT_EST


# Voice-stack launch gates — 0/4 clear. Stephanie is NOT launch-ready until
# these pass; the demo may proceed but must be labelled STAGED.
VOICE_LAUNCH_GATES: list[Gate] = [
    Gate(name="Waveform P95 latency", target="<90ms (interim <130ms)", current="~147ms", status="failing"),
    Gate(name="Caption drift P95", target="<2.0s (interim <2.5s)", current="~3.1s", status="failing"),
    Gate(name="LiveKit room stability", target="Pass", current="In testing", status="in_progress"),
    Gate(name="100-session load test", target="Pass", current="Not run (run 25→50→100)", status="pending"),
]

# Series A readiness — the missing items are evidence (receipts), not UI.
SERIES_A_GAPS: dict[str, str] = {
    "Financial Hygiene": "ERPNext reconciliation, CPA-reviewed financials, separate GC vs platform P&L",
    "Platform Revenue": "First paying Stephanie.ai customers, municipal pilot, ARR proof",
    "Technical Benchmarks": "Voice latency CSV exports, uptime report, anchor tx export, attestation pass/fail rate",
    "Data Room": "Financials, cap table, live benchmarks, customer contracts, pilot agreements",
}


# ---------------------------------------------------------------------------
# Risky-claim normalization (optimization report P0 #3)
# ---------------------------------------------------------------------------

class ClaimNormalization(BaseModel):
    """A risky claim and its compliant rewrite + credibility tag."""
    risky: str
    safe: str
    evidence: EvidenceTag


# Single source of truth for compliant claim language. Any surface (dashboard,
# deck, Notion) should render `safe`, never `risky`.
CLAIM_NORMALIZATIONS: list[ClaimNormalization] = [
    ClaimNormalization(
        risky="Series 7 Framework",
        safe="securities-analysis workflow framework; not licensed financial advice",
        evidence=EvidenceTag.HUMAN_GATED,
    ),
    ClaimNormalization(
        risky="Series 63 Framework",
        safe="state blue-sky compliance workflow framework; not licensed financial advice",
        evidence=EvidenceTag.HUMAN_GATED,
    ),
    ClaimNormalization(
        risky="CCIM Framework",
        safe="commercial real-estate investment-analysis framework; no human credential implied",
        evidence=EvidenceTag.MGMT_EST,
    ),
    ClaimNormalization(
        risky="1 Billion avatar deployment",
        safe="future-state avatar deployment architecture",
        evidence=EvidenceTag.SIMULATED,
    ),
    ClaimNormalization(
        risky="~3,000+ live validators",
        safe="distributed-node architecture (validator count unverified from chain data)",
        evidence=EvidenceTag.MGMT_EST,
    ),
    ClaimNormalization(
        risky="~82k holders and voters",
        safe="holder/voter governance architecture (count unverified from chain data)",
        evidence=EvidenceTag.MGMT_EST,
    ),
    ClaimNormalization(
        risky="~131,000 IQCore compute baseline",
        safe="benchmarked compute throughput (management estimate; CSV export pending)",
        evidence=EvidenceTag.MGMT_EST,
    ),
]

_CLAIM_INDEX = {c.risky.lower(): c for c in CLAIM_NORMALIZATIONS}


def normalize_claim(text: str) -> ClaimNormalization | None:
    """Return the compliant rewrite for a known risky claim, if any."""
    return _CLAIM_INDEX.get(text.strip().lower())


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
        "overall_platform_completion": OVERALL_PLATFORM_COMPLETION,
        "superseded_completion_figures": SUPERSEDED_COMPLETION_FIGURES,
        "platform_arr": PLATFORM_ARR,
        "platform_narrative": PLATFORM_NARRATIVE,
        "power_center": "construction operations",
        "next_unlock": "PermitStream + GCagent integration",
        "future_upside": "governance, tokenization, voice/avatar distribution",
        "voice_gates_clear": sum(1 for g in VOICE_LAUNCH_GATES if g.status == "passing"),
        "voice_gates_total": len(VOICE_LAUNCH_GATES),
        "components": [c.model_dump() for c in COMPONENT_STATUS],
        "voice_launch_gates": [g.model_dump() for g in VOICE_LAUNCH_GATES],
        "series_a_gaps": SERIES_A_GAPS,
        "claim_normalizations": [c.model_dump() for c in CLAIM_NORMALIZATIONS],
        "flywheels": [f.model_dump() for f in FLYWHEELS],
        "priority_phases": PRIORITY_PHASES,
    }
