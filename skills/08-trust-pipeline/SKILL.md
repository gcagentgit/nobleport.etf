---
name: trust-pipeline
description: Manages NoblePort customer relationships — customer summaries, job history, follow-up schedules, and membership/upsell opportunities — keeping HubSpot in sync. Use when a user needs a customer profile, a history of past jobs, a post-job follow-up schedule, or identification of repeat/membership opportunities. CRM writes are scoped and never blind-overwrite; customer messages pass a human review gate.
---

# Trust Pipeline Skill

**Tier 2 — NoblePort Operations · Status: STAGED (`hubspot_sync`) · gcagent module: `internal_ops_assistant`**

The relationship layer after the sale: it remembers customers, their job
history, and when to reach back out — turning one job into a lasting account.

## When to use

- A user needs a **customer summary** or profile.
- Someone wants a customer's **job history**.
- A completed job needs a **follow-up schedule** (warranty check-in, maintenance).
- A user asks where the **membership / repeat-work** opportunities are.

## Inputs

- HubSpot contact and company records (`hubspot_sync`, STAGED).
- Completed and active job history.
- Follow-up cadence and membership-offer policy.

## Outputs

- **Customer summary** — contact, properties, lifetime jobs, and value.
- **Job history** — past projects with outcomes and notes.
- **Follow-up schedule** — timed post-job touches.
- **Membership opportunities** — ranked upsell/retention candidates.

## Workflow

1. Resolve the customer across HubSpot and job records.
2. Assemble the summary and job history from linked sources.
3. Build the follow-up schedule from the cadence policy.
4. Identify membership/repeat opportunities from history and property data.
5. Draft any outreach; **route through human review before send.**

## Knowledge & data sources

- HubSpot via `backend/services/hubspot_sync.py` (`hubspot_sync`, STAGED).
- Job history from `construction_operations`.
- Pairs with `sales-router` (top of funnel) and `noblenest` (homeowner platform).

## Safety & approval gates

- CRM writes are **scoped to owned fields**; conflicts raise, they don't merge.
- Customer-visible communications require human review before send.
- Membership offers are suggestions for a human to extend, not auto-sent.

## Success criteria

- Customer summaries reconcile across HubSpot and job records.
- Follow-up schedules have concrete dates and reasons.
- Opportunity ranking is explainable from history, not asserted.

## Failure modes

- `crm_field_overwrite` — blind-overwriting a HubSpot field.
- `duplicate_contact` — creating a duplicate instead of resolving the existing one.
- `lost_context_across_channels` — follow-ups that ignore prior interactions.
