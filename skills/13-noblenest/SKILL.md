---
name: noblenest
description: Powers the NobleNest homeowner platform — maintenance plans, property condition reports, and upgrade recommendations for homeowners. Use when a user wants a maintenance schedule for a home, a property report, or prioritized upgrade recommendations. Advisory homeowner guidance only; it does not constitute an inspection, warranty, or professional engineering assessment.
---

# NobleNest Skill

**Tier 3 — Growth Engine · Status: MODELED · gcagent module: `internal_ops_assistant`**

The homeowner-facing layer: it keeps a relationship alive between jobs by
helping owners maintain and improve their property — feeding repeat work into
`trust-pipeline`.

## When to use

- A homeowner needs a **maintenance plan** / seasonal schedule.
- A **property condition report** is requested.
- A homeowner wants **upgrade recommendations** prioritized by value.

## Inputs

- Property profile (age, systems, materials, prior NoblePort jobs).
- Homeowner goals (comfort, efficiency, resale, accessibility).
- Regional/seasonal factors (Massachusetts climate).

## Outputs

- **Maintenance plan** — seasonal tasks with cadence.
- **Property report** — condition summary and watch items.
- **Upgrade recommendations** — ranked by value, cost, and urgency.

## Workflow

1. Build the property profile from records and prior job history.
2. Generate the seasonal maintenance plan for the climate and systems.
3. Summarize condition and flag watch items.
4. Rank upgrades by value, cost (via `estimator`), and urgency.
5. Present as homeowner guidance; route any service offer through human review.

## Knowledge & data sources

- Property and job history (`construction_operations`, `trust-pipeline`).
- Massachusetts seasonal/maintenance norms.
- `building-code` for upgrade code implications; `estimator` for cost ranges.

## Safety & approval gates

- **Advisory only** — guidance is not a home inspection, warranty, or PE assessment.
- Condition assessments based on records are clearly distinguished from on-site findings.
- Upgrade recommendations are suggestions; service offers pass human review before send.

## Success criteria

- Maintenance plans fit the property's systems and the local climate.
- Upgrade rankings expose value, cost, and urgency inputs.
- The advisory (non-inspection) boundary is explicit.

## Failure modes

- `report_implies_inspection` — record-based output read as an on-site inspection.
- `upgrade_without_cost_context` — a recommendation with no cost framing.
- `unsolicited_service_push` — auto-sending offers without human review.
