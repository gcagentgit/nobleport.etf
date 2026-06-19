# NoblePort Workspace Skill Library

A portable library of **15 operator skills** that compose NoblePort's domain
knowledge into discrete, loadable units of work. Each skill is a folder under
`skills/` containing a `SKILL.md` with model-routable frontmatter (`name`,
`description`) and a grounded body (when to use, inputs, outputs, workflow,
safety gates, success criteria, failure modes).

These skills are the **operator-facing** companion to the engineering-facing
[`gcagent/`](../gcagent/README.md) capability registry. Where `gcagent` defines
the 12 always-on *engineering* competencies and 5 domain modules, this library
packages the day-to-day *business* workflows of NoblePort Construction so they
can be invoked, versioned, and improved one at a time.

## Truth-Layer discipline

Every skill carries a status tag mirroring
[`backend/config/operational_truth.py`](../backend/config/operational_truth.py)
and the Truth Label in
[`docs/strategy/four-layers-framework.md`](../docs/strategy/four-layers-framework.md):

| Tag | Meaning |
|---|---|
| **LIVE** | Running in production today. |
| **STAGED** | Built, human-gated, not yet fully autonomous. |
| **MODELED** | Designed/analytical; not an executing production surface. |
| **REFERENCE** | Advisory knowledge; never a substitute for a licensed professional or AHJ. |

No skill may present a STAGED, MODELED, or REFERENCE capability as LIVE. No skill
fabricates metrics, validator counts, or uptime figures — see the Public Claim
Freeze discipline. AI **drafts, analyzes, and routes**; humans decide every
regulated, financial, legal, engineering, and licensing action via the
[`HumanApprovalGateway`](../contracts/HumanApprovalGateway.sol) and the
[Stephanie governance gate](../docs/governance/stephanie-ai-architecture-v2.md).

## The library

### Tier 1 — Core Construction (highest ROI)

| # | Skill | Status | Purpose |
|---|---|---|---|
| 01 | [estimator](01-estimator/SKILL.md) | LIVE | Estimates, proposals, change orders, payment schedules |
| 02 | [permitstream](02-permitstream/SKILL.md) | STAGED | Permit intelligence and lead identification (MA) |
| 03 | [project-manager](03-project-manager/SKILL.md) | LIVE | Daily logs, scheduling, material & sub coordination |
| 04 | [building-code](04-building-code/SKILL.md) | REFERENCE | IRC/IBC + Massachusetts code interpretation |
| 05 | [structural-review](05-structural-review/SKILL.md) | REFERENCE | Framing takeoffs and structural material lists |

### Tier 2 — NoblePort Operations

| # | Skill | Status | Purpose |
|---|---|---|---|
| 06 | [stephanie-executive](06-stephanie-executive/SKILL.md) | STAGED | Executive briefings, KPI and risk reporting |
| 07 | [sales-router](07-sales-router/SKILL.md) | LIVE | Lead stage management and conversion analysis |
| 08 | [trust-pipeline](08-trust-pipeline/SKILL.md) | STAGED | Customer relationship management and follow-up |
| 09 | [change-orders](09-change-orders/SKILL.md) | LIVE | Scope control with audit trail and approval routing |
| 10 | [payment-node](10-payment-node/SKILL.md) | STAGED | Draw schedules, deposit validation, retention |

### Tier 3 — Growth Engine

| # | Skill | Status | Purpose |
|---|---|---|---|
| 11 | [content-engine](11-content-engine/SKILL.md) | STAGED | Turn projects into marketing content (draft-only) |
| 12 | [real-estate-development](12-real-estate-development/SKILL.md) | MODELED | Feasibility, valuation, ADU and rental analysis |
| 13 | [noblenest](13-noblenest/SKILL.md) | MODELED | Homeowner maintenance and upgrade platform |
| 14 | [recruiting](14-recruiting/SKILL.md) | STAGED | Hiring and subcontractor onboarding |
| 15 | [sop](15-sop/SKILL.md) | LIVE | Standard operating procedures and checklists |

## First five to deploy

Per the source plan, the five skills that cover ~80% of daily operational
workload are **estimator, project-manager, building-code, structural-review,
and stephanie-executive**.

## Skill contract

Each `SKILL.md` satisfies this shape:

```
---
name: <lowercase-hyphen slug, matches folder>
description: Third-person summary plus explicit "Use when…" triggers.
---
# <Title> Skill
**Tier · Status · Related gcagent module**
## When to use
## Inputs
## Outputs
## Workflow
## Knowledge & data sources
## Safety & approval gates
## Success criteria
## Failure modes
```

## Adding a skill

1. Create `skills/NN-<slug>/SKILL.md` with the contract above.
2. Assign an honest status tag from `operational_truth.py`.
3. Declare the human-approval gate for any regulated, financial, or legal output.
4. Add a row to the table in this README.
