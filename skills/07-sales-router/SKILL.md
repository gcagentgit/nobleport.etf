---
name: sales-router
description: Manages the NoblePort sales pipeline — routing leads through New Lead, Qualified, Inspection, Estimate, Closed Won, and Nurture stages, and producing follow-up plans and conversion analysis. Use when a user needs to advance or triage a lead, build a follow-up sequence, or analyze pipeline conversion. Customer-facing communications are drafted and pass a human review gate before send.
---

# Sales Router Skill

**Tier 2 — NoblePort Operations · Status: LIVE (`lead_pipeline`) · gcagent module: `internal_ops_assistant`**

Moves leads through the pipeline and tells the team where to spend attention.
This is the **Lead → Intake** entry to the revenue spine.

## When to use

- A new lead needs **routing** into the pipeline.
- A lead needs to **advance** a stage (or be triaged/nurtured).
- A **follow-up plan** is needed for a deal.
- Someone asks for **conversion analysis** across the pipeline.

## Inputs

- Inbound lead (source, contact, scope interest).
- Current pipeline state from `lead_pipeline` (LIVE) and HubSpot.
- Stage definitions and follow-up cadence policy.

## Outputs

- **Stage routing** — the lead placed in the correct stage with rationale.
- **Follow-up plan** — next touch, channel, and timing.
- **Conversion analysis** — stage-to-stage conversion and drop-off points.

## Workflow

1. Classify the lead and place it in a stage:
   **New Lead → Qualified → Inspection → Estimate → Closed Won**, or **Nurture**.
2. Generate the follow-up plan for the current stage.
3. Hand inspection/estimate steps to `project-manager` / `estimator`.
4. For conversion questions, compute stage transitions from pipeline data.
5. Draft any customer-facing message; **route it through human review before send.**

## Knowledge & data sources

- `lead_pipeline` (LIVE) — capture, CRM sync, pipeline management.
- HubSpot CRM via `backend/services/hubspot_sync.py` (`hubspot_sync`, STAGED).
- Pairs with `trust-pipeline` for relationship/CRM depth.

## Safety & approval gates

- **External communications require human review** before they go out.
- CRM writes are scoped to owned fields; never blind-overwrite a record.
- Conversion figures come from real pipeline data, never illustrative numbers.

## Success criteria

- Each lead's stage placement has an explainable rationale.
- Follow-up plans have a concrete next touch, channel, and date.
- Conversion analysis ties to linked source records.

## Failure modes

- `premature_customer_send` — a draft going out without human review.
- `crm_field_overwrite` — clobbering a field the skill doesn't own.
- `illustrative_conversion_number` — a made-up rate presented as measured.
