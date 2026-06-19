---
name: estimator
description: Builds construction estimates, proposals, change orders, and payment schedules for roofing, additions, decks, and bathrooms using NoblePort cost templates, labor rates, and material markups. Use when a user needs to price a job, draft a proposal, produce a change-order cost, or lay out a deposit/draw schedule under Massachusetts Home Improvement Contractor rules.
---

# Estimator Skill

**Tier 1 — Core Construction · Status: LIVE (`estimate_generation`) · gcagent module: `construction_operations`**

Turns a scope of work into a priced, send-ready estimate and the payment terms
that go with it. This is the revenue spine's first paid step:
`Lead → Intake → **Estimate** → Permit → Build → Invoice → Closeout`.

## When to use

- A homeowner or lead needs a price for roofing, an addition, a deck, or a bathroom.
- An existing job needs a **change order** priced against the original contract.
- A proposal needs a **payment schedule** (deposit + progress draws).
- Someone asks "what should we charge for…" or "build the proposal for…".

## Inputs

- Scope of work (measurements, materials, finish level).
- Cost templates, current labor rates, material unit costs.
- Markup policy (material markup %, target gross-profit floor).
- Job location (drives tax, permit, and travel assumptions).

## Outputs

- **Estimate / proposal** — line-itemed by labor, material, and markup.
- **Change order** — delta scope with cost impact and revised contract total.
- **Payment schedule** — deposit + progress draws.
- A gross-profit summary flagged against the GP floor (`job_cost_forecasting`, MODELED).

## Workflow

1. Normalize the scope into measurable line items (SF, LF, count, EA).
2. Apply labor rates and material unit costs from the active cost template.
3. Apply material markup and overhead; compute gross profit and margin.
4. Compare margin to the GP floor; flag (do not silently accept) any shortfall.
5. Generate the payment schedule within Massachusetts HIC limits (below).
6. Emit a draft. **A human reviews and signs before it becomes a contract.**

## Knowledge & data sources

- NoblePort cost templates, labor rates, material markups.
- Massachusetts Home Improvement Contractor law (M.G.L. c.142A): contracts over
  $1,000 must be written; deposits are capped (no more than **1/3 of total**, or
  the cost of special-order materials, whichever is greater).
- `estimate_generation` (LIVE) for creation/sending/tracking; `treasury_workflows`
  (STAGED) for downstream invoicing.

## Safety & approval gates

- Output is a **draft**. It is not a binding contract until a human signs it.
- Payment schedules must respect the MA HIC deposit cap — never propose a deposit
  above the statutory limit.
- Never invent prices for unknown materials; surface the gap and ask.
- Margin below the GP floor escalates for human pricing review; it is not buried.

## Success criteria

- Every line item is traceable to a rate or unit cost, not a guess.
- The proposal's gross profit and margin are stated explicitly.
- The payment schedule is HIC-compliant and reconciles to the contract total.

## Failure modes

- `silent_margin_erosion` — accepting a below-floor margin without flagging it.
- `deposit_over_statutory_cap` — proposing a deposit above the MA HIC limit.
- `hallucinated_unit_cost` — pricing a material the template doesn't cover.
