---
name: building-code
description: Interprets building code for residential and light-commercial construction — IRC, IBC, Massachusetts amendments (780 CMR), energy code, and the deck, stair, egress, and ADU provisions. Use when a user asks whether something meets code, what a code section requires, or how a Massachusetts amendment changes a base IRC/IBC rule. Advisory reference only — never a substitute for a licensed design professional or the AHJ.
---

# Building Code Skill

**Tier 1 — Core Construction · Status: REFERENCE (advisory) · Supports: `compliance_documentation`**

Answers code-interpretation questions and flags compliance risk early, with
every answer pinned to a specific code section and edition.

## When to use

- "Does this deck / stair / guard / egress detail meet code?"
- "What does the Massachusetts amendment change versus base IRC/IBC?"
- "What are the ADU requirements here?"
- A design or estimate needs a code check before it goes further.

## Inputs

- The specific detail or assembly in question.
- Jurisdiction (Massachusetts; specific AHJ when it matters).
- Occupancy / use and construction type, when relevant.

## Outputs

- A code answer with the **section number and code edition** cited.
- The applicable **Massachusetts amendment** (780 CMR) where it overrides base code.
- A short list of compliance risks or follow-ups for the AHJ.

## Workflow

1. Identify the governing code(s): IRC vs. IBC by occupancy/size.
2. Apply the Massachusetts amendments (780 CMR) and energy code overlay.
3. Pull the controlling provision for decks, stairs, guards, egress, or ADU.
4. State the requirement, cite section + edition, and note any AHJ discretion.
5. Flag anything that needs a licensed design professional or AHJ ruling.

## Knowledge & data sources

- IRC and IBC (base model codes).
- Massachusetts State Building Code (780 CMR) amendments and the MA energy code.
- Deck, stair, guard, egress, and Massachusetts ADU provisions.

## Safety & approval gates

- **Advisory only.** This skill interprets code; it does not certify designs,
  stamp drawings, or replace the Authority Having Jurisdiction.
- Every claim cites its section and edition — no uncited code assertions.
- Structural sizing belongs to `structural-review` and ultimately a licensed PE.
- When the code is ambiguous or AHJ-discretionary, say so explicitly.

## Success criteria

- Each answer resolves to a real, current code section with the edition named.
- Massachusetts amendments are applied, not just the base model code.
- Ambiguities are surfaced, not papered over with false certainty.

## Failure modes

- `uncited_code_claim` — asserting a requirement without a section reference.
- `stale_edition` — quoting a superseded code cycle.
- `amendment_missed` — applying base IRC/IBC where MA (780 CMR) overrides it.
