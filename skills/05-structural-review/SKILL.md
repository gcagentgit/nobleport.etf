---
name: structural-review
description: Performs preliminary structural takeoffs for wood-framed construction — LVLs, I-joists, headers, footings, beam sizing, and framing layouts — producing material lists, framing schedules, and structural summaries. Use when a user needs a framing material list, a header or beam size sanity-check, or a structural summary for an estimate. Advisory only — load-bearing changes require a licensed professional engineer's stamp.
---

# Structural Review Skill

**Tier 1 — Core Construction · Status: REFERENCE (advisory) · Supports: `estimator`, `construction_operations`**

Produces preliminary framing takeoffs and material lists so estimates and
schedules can proceed — explicitly upstream of, and subordinate to, a licensed
engineer's sealed design.

## When to use

- An estimate needs a **framing material list** or **framing schedule**.
- A header, beam, LVL, or footing needs a **preliminary sizing sanity-check**.
- A scope needs a **structural summary** before pricing or scheduling.

## Inputs

- Spans, tributary widths, and loading assumptions.
- Member type under consideration (LVL, I-joist, dimensional lumber, steel).
- Framing layout or plan, when available.

## Outputs

- **Material list** — members, sizes, counts, and connectors.
- **Framing schedule** — joists, headers, beams by location.
- **Structural summary** — assumptions, preliminary sizes, and what needs a PE.

## Workflow

1. Capture spans, loads, and tributary areas explicitly.
2. Produce **preliminary** member sizes from published span tables.
3. Assemble the material list and framing schedule.
4. State every load and span assumption used.
5. Flag every load-bearing element that **requires a licensed PE's stamp**.

## Knowledge & data sources

- Manufacturer span tables (LVL, I-joist) and code-referenced lumber tables.
- Header, footing, and beam sizing references for residential framing.
- Pairs with `building-code` for code-driven minimums (`job_cost_forecasting`,
  MODELED, for downstream cost variance).

## Safety & approval gates

- **Not engineering certification.** Outputs are preliminary takeoffs for
  estimating and ordering, not a sealed structural design.
- Any load-bearing modification, beam, or header on a real project requires a
  **licensed professional engineer's stamp** before construction.
- Every size is shown with the span/load assumption behind it; no bare numbers.
- When loads are unknown or unusual, stop and request a PE — do not guess.

## Success criteria

- Material lists reconcile to the framing layout and the estimate takeoff.
- Every preliminary size is traceable to a span table and stated assumption.
- The "requires PE stamp" boundary is explicit on every load-bearing item.

## Failure modes

- `preliminary_size_taken_as_final` — a sanity-check size used as the design.
- `unstated_load_assumption` — a size given without its governing load/span.
- `pe_stamp_boundary_omitted` — failing to flag work that needs an engineer.
