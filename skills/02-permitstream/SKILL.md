---
name: permitstream
description: Produces permit intelligence for Massachusetts municipalities — permit summaries, municipality reports, lead identification, and opportunity scoring for roofing, additions, renovations, and ADUs (Essex County focus). Use when a user wants to find permitting leads, summarize recent permit activity in a town, or score a permit opportunity. Scraped data is STAGED and must be verified with the AHJ before action.
---

# PermitStream Skill

**Tier 1 — Core Construction · Status: STAGED (`permit_scraping`); forecasting MODELED (`permit_forecast`) · Surface: PermitStream.ai**

Turns public municipal permit activity into ranked construction leads and
municipality-level reports, focused on Massachusetts (Essex County first).

## When to use

- A user wants new construction **leads** from recent permit filings.
- Someone needs a **summary** of permit activity for a town or address.
- A permit opportunity needs an **opportunity score** to prioritize outreach.
- A user asks about ADU, roofing, addition, or renovation permits in MA.

## Inputs

- Target municipality / county (default: Essex County, MA).
- Permit type filter (roofing, additions, renovations, ADU).
- Time window and address or parcel, when known
  (e.g. parcel `R26-0-12`, 236 High Road, Newbury — permit `21-329RB`).

## Outputs

- **Permit summary** — type, value, status, applicant, address, dates.
- **Lead identification** — properties whose permits signal a buying window.
- **Municipality report** — issuance volume and mix for a town.
- **Opportunity score** — ranked priority for outreach (with the inputs shown).

## Workflow

1. Pull or refresh permit records for the target AHJ (`permit_scraping`, STAGED).
2. Normalize fields (type, value, status, dates, applicant, parcel).
3. Classify each record by NoblePort service line.
4. Score opportunity from permit value, type fit, recency, and locality.
5. Emit summaries/reports. **Verify any scraped figure against the AHJ before acting.**

## Knowledge & data sources

- Massachusetts municipal permit portals (geo-constrained to MA).
- Essex County parcel and assessor data (see `docs/realty/236-high-road-newbury.md`).
- `permit_forecast` (MODELED) for AHJ issuance-time estimates — labeled as modeled,
  never presented as a live SLA.

## Safety & approval gates

- Scraped permit data may lag the official record — **verify with the AHJ** before
  outreach or any commitment.
- This skill never **submits** a permit; submission is a human, AHJ-facing action.
- Lead outreach copy is draft-only and passes through the sales/human review gate.
- Respect each portal's terms of use and rate limits.

## Success criteria

- Every lead resolves to a real, current permit record.
- Opportunity scores expose their inputs (value, type, recency, locality).
- Forecasts are clearly tagged MODELED, never sold as guaranteed timelines.

## Failure modes

- `stale_permit_state` — acting on a scraped status the AHJ has since changed.
- `forecast_presented_as_sla` — treating a modeled estimate as a commitment.
- `geo_scope_leak` — scoring opportunities outside the supported MA geography.
