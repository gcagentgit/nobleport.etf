---
name: real-estate-development
description: Performs development analysis for property opportunities — feasibility studies, land valuation, ADU analysis, and rental projections — grounded in assessor data and comparable sales. Use when a user wants to evaluate a parcel's development potential, value land, assess an ADU, or project rental income. Informational only: not legal, financial, or real-estate advice, and AVM estimates (Zillow/Redfin) are treated as unreliable.
---

# Real Estate Development Skill

**Tier 3 — Growth Engine · Status: MODELED (analytical) · References: `docs/realty/`, `src/lib/realty/`**

Analyzes whether a property is worth developing — the bridge from construction
operations toward NoblePort Realty, kept strictly advisory.

## When to use

- A parcel needs a **feasibility study** for development.
- **Land valuation** is required (and AVMs aren't trustworthy for the parcel).
- An **ADU** opportunity needs analysis.
- **Rental projections** are needed for a hold scenario.

## Inputs

- Parcel data: assessor record, zoning, lot size, existing structures
  (e.g. 236 High Road, Newbury — parcel `R26-0-12`, R-AG zoning, Essex County).
- Comparable sales and local rent data.
- Development scenario (ADU, addition, new build, hold-and-rent).

## Outputs

- **Feasibility study** — scenario, constraints, rough cost, and upside.
- **Land valuation** — grounded in assessed value and real comps.
- **ADU analysis** — zoning fit, cost, and added value/income.
- **Rental projection** — income, expenses, and yield with assumptions shown.

## Workflow

1. Pull assessor, zoning, and parcel facts; note data confidence.
2. Build the development scenario against zoning constraints.
3. Value the land from **assessed value and comparable sales**, not AVMs.
4. Project costs (via `estimator`) and income with explicit assumptions.
5. Present as analysis, clearly labeled informational — not advice.

## Knowledge & data sources

- NoblePort Realty research assets (`docs/realty/236-high-road-newbury.md`),
  mirrored by `src/lib/realty/property-analysis.ts`.
- Essex County / Massachusetts assessor and zoning data.
- `building-code` for ADU/zoning rules; `permitstream` for permit context.

## Safety & approval gates

- **Informational only** — not legal, financial, or real-estate advice. Verify
  every data point independently before any decision.
- **AVMs are unreliable** (e.g. a $577,600 Zestimate on a $52,700-assessed
  accessory parcel) — prefer assessed value and comps, and say why.
- Every projection states its assumptions; no single-number certainty.

## Success criteria

- Valuations rest on assessed value and real comps, with confidence noted.
- Projections show their assumptions and a sensitivity range.
- The informational-only framing is explicit.

## Failure modes

- `avm_taken_as_truth` — using a Zestimate/Redfin figure as a real value.
- `projection_without_assumptions` — a yield number with no stated basis.
- `advice_framing` — presenting analysis as financial or legal advice.
