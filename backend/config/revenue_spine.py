"""
Revenue Spine

The core operational workflow that everything else supports.
Every feature, agent, and integration exists to accelerate this sequence:

    Lead → Intake → Estimate → Permit → Build → Invoice → Closeout

This module defines the canonical stages, their gates, and the system
surfaces that power each transition. The revenue spine is the product.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SpineStage(str, Enum):
    LEAD = "lead"
    INTAKE = "intake"
    ESTIMATE = "estimate"
    PERMIT = "permit"
    BUILD = "build"
    INVOICE = "invoice"
    CLOSEOUT = "closeout"


@dataclass(frozen=True)
class StageGate:
    """Condition that must be met before advancing to the next stage."""
    name: str
    enforced: bool
    human_required: bool


@dataclass(frozen=True)
class SpineStageConfig:
    stage: SpineStage
    display_name: str
    systems: tuple[str, ...]
    gates: tuple[StageGate, ...]
    kpis: tuple[str, ...]


REVENUE_SPINE: tuple[SpineStageConfig, ...] = (
    SpineStageConfig(
        stage=SpineStage.LEAD,
        display_name="Lead Capture",
        systems=("Stephanie.ai", "HubSpot", "Website"),
        gates=(
            StageGate("contact_info_captured", enforced=True, human_required=False),
            StageGate("project_type_classified", enforced=True, human_required=False),
        ),
        kpis=("lead_volume", "response_time_hours", "source_attribution"),
    ),
    SpineStageConfig(
        stage=SpineStage.INTAKE,
        display_name="Project Intake",
        systems=("Stephanie.ai", "LiveKit", "Google Calendar"),
        gates=(
            StageGate("voice_intake_completed", enforced=True, human_required=False),
            StageGate("site_visit_scheduled", enforced=False, human_required=True),
            StageGate("scope_documented", enforced=True, human_required=False),
        ),
        kpis=("intake_completion_rate", "avg_intake_duration_min", "homeowner_nps"),
    ),
    SpineStageConfig(
        stage=SpineStage.ESTIMATE,
        display_name="Estimate & Proposal",
        systems=("GCagent.ai", "Backend", "Stripe"),
        gates=(
            StageGate("estimate_generated", enforced=True, human_required=False),
            StageGate("estimate_reviewed_by_pm", enforced=True, human_required=True),
            StageGate("proposal_sent", enforced=True, human_required=True),
            StageGate("deposit_collected", enforced=True, human_required=False),
        ),
        kpis=("estimate_turnaround_days", "win_rate", "avg_deal_value"),
    ),
    SpineStageConfig(
        stage=SpineStage.PERMIT,
        display_name="Permitting",
        systems=("PermitStream.ai", "AHJ Portals"),
        gates=(
            StageGate("permit_application_prepared", enforced=True, human_required=False),
            StageGate("permit_submitted_by_human", enforced=True, human_required=True),
            StageGate("permit_issued", enforced=True, human_required=False),
        ),
        kpis=("permit_cycle_days", "correction_rate", "ahj_median_days"),
    ),
    SpineStageConfig(
        stage=SpineStage.BUILD,
        display_name="Construction",
        systems=("GCagent.ai", "Buildertrend", "Field Crews"),
        gates=(
            StageGate("mobilization_complete", enforced=True, human_required=True),
            StageGate("gp_above_floor", enforced=True, human_required=False),
            StageGate("inspections_passed", enforced=True, human_required=True),
        ),
        kpis=("schedule_variance_days", "gp_forecast_pct", "rfi_resolution_days"),
    ),
    SpineStageConfig(
        stage=SpineStage.INVOICE,
        display_name="Invoicing & Collections",
        systems=("Backend", "Stripe", "QuickBooks"),
        gates=(
            StageGate("milestone_invoiced", enforced=True, human_required=False),
            StageGate("payment_received", enforced=True, human_required=False),
        ),
        kpis=("ar_days", "collection_rate", "overdue_amount"),
    ),
    SpineStageConfig(
        stage=SpineStage.CLOSEOUT,
        display_name="Project Closeout",
        systems=("GCagent.ai", "Backend"),
        gates=(
            StageGate("punch_list_complete", enforced=True, human_required=True),
            StageGate("final_invoice_paid", enforced=True, human_required=False),
            StageGate("warranty_docs_delivered", enforced=True, human_required=True),
        ),
        kpis=("closeout_cycle_days", "final_gp_pct", "client_satisfaction"),
    ),
)


def get_stage(stage: SpineStage) -> SpineStageConfig:
    for config in REVENUE_SPINE:
        if config.stage == stage:
            return config
    raise ValueError(f"Unknown stage: {stage}")


def get_human_required_gates() -> list[tuple[SpineStage, StageGate]]:
    """All gates across the spine that require human action."""
    return [
        (config.stage, gate)
        for config in REVENUE_SPINE
        for gate in config.gates
        if gate.human_required
    ]


def get_enforced_gates() -> list[tuple[SpineStage, StageGate]]:
    """All gates that are currently enforced (blocking advancement)."""
    return [
        (config.stage, gate)
        for config in REVENUE_SPINE
        for gate in config.gates
        if gate.enforced
    ]
