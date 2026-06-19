---
name: recruiting
description: Supports hiring and subcontractor onboarding — drafting job descriptions, interview scorecards, and trade qualification reviews, and verifying licensing/insurance. Use when a user needs a job description, a structured interview scorecard, or a subcontractor qualification review. The agent drafts and structures; humans make hiring decisions, and credentials (MA HIC, insurance, COI) must be verified with the issuing authority.
---

# Recruiting Skill

**Tier 3 — Growth Engine · Status: STAGED (draft-only) · gcagent module: `internal_ops_assistant`**

Helps NoblePort hire employees and onboard subcontractors with structure and
credential discipline — supporting Layer 2 contractor onboarding.

## When to use

- A role needs a **job description**.
- An interview needs a **structured scorecard**.
- A subcontractor needs a **trade qualification review** before onboarding.

## Inputs

- Role or trade requirements.
- Candidate / subcontractor materials (resume, license #, insurance, references).
- Hiring policy and qualification criteria.

## Outputs

- **Job descriptions** — responsibilities, requirements, qualifications.
- **Interview scorecards** — structured, criteria-based evaluation forms.
- **Trade qualification reviews** — license, insurance, and experience checks.

## Workflow

1. Capture the role/trade requirements and qualification bar.
2. Draft the job description or scorecard from the criteria.
3. For subs, assemble a qualification review: license, insurance, references.
4. Flag any credential that must be **verified with the issuing authority**.
5. Present for a human hiring decision; the agent does not decide.

## Knowledge & data sources

- Massachusetts HIC / CSL licensing context (verification, not assertion).
- Insurance requirements (workers' comp, general liability, COI).
- Hiring policy and trade qualification criteria.

## Safety & approval gates

- **The agent does not make hiring decisions** — it drafts and structures only.
- Credentials (MA HIC/CSL, insurance, COI) must be **verified with the issuer**;
  the agent never self-attests a license as valid.
- Job descriptions and evaluations follow equal-opportunity / non-discrimination norms.
- Candidate data is handled as confidential PII.

## Success criteria

- Job descriptions map cleanly to the stated role requirements.
- Scorecards are criteria-based and consistently applied.
- Qualification reviews mark each credential as verified or pending verification.

## Failure modes

- `unverified_credential_accepted` — treating a claimed license as confirmed.
- `automated_hiring_decision` — the agent advancing/rejecting on its own.
- `biased_criteria` — evaluation criteria that risk discrimination.
