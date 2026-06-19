---
name: content-engine
description: Turns completed project material — photos, videos, and daily logs — into marketing content (Facebook posts, LinkedIn articles, website case studies, reels). Use when a user wants to turn a finished job into social content, a case study, or a short-form video script. All output is draft-only and passes a human review gate before publishing; no fabricated metrics or claims, and customer/PII consent is required.
---

# Content Engine Skill

**Tier 3 — Growth Engine · Status: STAGED (draft-only) · gcagent module: `reporting_automation`**

Converts real project work into marketing assets — feeding Layer 4 (Market
Demand) with proof of actual construction, not narrative.

## When to use

- A finished job has **photos/videos/logs** worth turning into content.
- A user wants a **Facebook post, LinkedIn article, case study, or reel script**.
- The team needs before/after content from a project's daily logs.

## Inputs

- Project photos and videos (with consent to use).
- Daily logs and project outcomes (`project-manager`).
- Brand voice and channel guidelines.

## Outputs

- **Facebook posts** and **LinkedIn articles**.
- **Website case studies** (problem → approach → result).
- **Reel / short-form video scripts**.

## Workflow

1. Pull the project's real materials and outcome from daily logs.
2. Confirm media consent and that no private customer data is exposed.
3. Draft channel-appropriate content grounded in what actually happened.
4. Keep claims truthful — no invented stats, timelines, or testimonials.
5. **Route every asset through human review before publishing.**

## Knowledge & data sources

- Project media and daily logs from `construction_operations`.
- Brand and channel guidelines.
- Public Claim Freeze discipline (no fabricated metrics or exaggerated figures).

## Safety & approval gates

- **Draft-only.** Nothing publishes without human review and approval.
- **Consent required** for customer photos, addresses, and identifying details.
- **No fabricated claims** — figures, awards, and testimonials must be real and
  verifiable, consistent with the Public Claim Freeze.
- Strip PII and private project details before anything goes public.

## Success criteria

- Every published claim is grounded in a real project fact.
- Media used has documented consent.
- Content matches brand voice and the target channel's format.

## Failure modes

- `unconsented_media` — publishing customer photos without permission.
- `fabricated_marketing_claim` — invented stats or testimonials.
- `pii_leak` — exposing addresses or private details in public content.
