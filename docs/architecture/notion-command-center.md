# NoblePort / Stephanie.ai — Notion Command Center ↔ Backend

Notion is the **human control layer**. The backend is the execution layer.
This document maps the two and records the locked decisions from the
optimization report. **The live connector is deferred** (per decision) — this
is the spec for when it's built. First target when greenlit: **status
dashboards** (read-mostly, one-way push from the truth registry).

## The Command Center (verified reachable via MCP)

Main page: `🏗️ NoblePort Workflow Command Center`
(`37ac922d7b4a81bb8611dc25da554cf7`)

| Notion database | data source | Backend counterpart |
| --- | --- | --- |
| Workflow Control Board | `collection://f2a9cb06-0248-4e29-a74f-07a65903cf6b` | `backend/core/revenue_loop.py` stages |
| Jobs / Projects Pipeline | `collection://4aed1ba8-16ef-45dd-94d6-291bb84b692c` | `Project` / `Job` models + GCagent |
| Approval Log | `collection://6c74e33b-d183-460f-9e5d-22306b0f3825` | Cyborg `HUMAN_REQUIRED_ACTIONS` + self-improvement `approve/reject` + AuditBeacon |
| Platform Module Status | `collection://9e1f3571-4c82-4e85-96a4-e7ef2d155d10` | `truth_registry.COMPONENT_STATUS` |
| Voice Launch Gates | `collection://0e6bd1b7-c90e-4695-9158-897d9134a084` | `truth_registry.VOICE_LAUNCH_GATES` |
| Series A Readiness Gates | `collection://d4447203-a94a-4ac0-adf1-18a58102acc8` | `truth_registry.SERIES_A_GAPS` |
| Stephanie Matrix Truth Register | `collection://968aa7d6-88ac-4945-8719-6edb1fa749c6` | `truth_registry.CLAIM_NORMALIZATIONS` |

The Notion **Operating Rule** ("Stephanie drafts/routes/recommends; Michael
approves contracts, payments, permit submissions, regulated filings, financial
actions") is the same text as `truth_registry.CONTROL_RULE`, enforced in code
by `ControlMode.FAIL_CLOSED`.

## Label vocabulary — reconciled to one source

Three places used three label sets. They are reconciled in code so every
surface reads the same thing:

**State** (`TruthLabel`, deployment/operational state):
`LIVE · STAGED · SIMULATED · BLOCKED · TARGET · PENDING`
— now includes `BLOCKED` to match Notion and the report.

**Evidence** (`EvidenceTag`, credibility of a *number/claim*, orthogonal):
`VERIFIED · MGMT_EST · SIMULATED · BLOCKED · HUMAN_GATED`
— this is the report's discipline: a dashboard must not render management
estimates, technical claims, and future-state in the same visual language.
Every `ComponentStatus` carries an `evidence` tag (default `MGMT_EST`).

| Report badge | Code |
| --- | --- |
| VERIFIED | `EvidenceTag.VERIFIED` |
| STAGED | `TruthLabel.STAGED` |
| MGMT EST | `EvidenceTag.MGMT_EST` |
| SIMULATED | `TruthLabel.SIMULATED` / `EvidenceTag.SIMULATED` |
| BLOCKED | `TruthLabel.BLOCKED` / `EvidenceTag.BLOCKED` |
| HUMAN-GATED | `EvidenceTag.HUMAN_GATED` |

## Locked decisions from the optimization report (now in code)

- **One completion number.** `OVERALL_PLATFORM_COMPLETION = 46`; `48` is in
  `SUPERSEDED_COMPLETION_FIGURES`. The conflicting header figure is retired.
- **Narrative.** `PLATFORM_ARR = 0`, `PLATFORM_NARRATIVE =
  "pre-Series A preparation / strategic seed narrative"`. Never framed as traction.
- **Module badges.** Each platform module carries a `tier`
  (Stephanie LAUNCH-CRITICAL, GCagent/PermitStream PHASE 2, Cyborg PHASE 3,
  Discord DEFERRED).
- **Voice stack is the launch bottleneck.** `VOICE_LAUNCH_GATES` — 0/4 clear.
  Stephanie demos must be labelled `STAGED`, not launch-ready.
- **Risky-claim normalization.** `CLAIM_NORMALIZATIONS` + `normalize_claim()`
  rewrite licensing/credential/future-state claims into compliant language
  ("Series 7 Framework" → "securities-analysis workflow framework; not licensed
  financial advice"; "1 Billion avatar deployment" → "future-state avatar
  deployment architecture"; unverified validator/holder counts flagged).

`registry_snapshot()` exposes all of the above for any surface.

## Connector plan (deferred)

When greenlit, build `backend/services/notion_sync.py` (mirroring
`hubspot_sync.py`) + `backend/api/notion.py`. **First target: status
dashboards**, one-way push from `registry_snapshot()`:

- Platform Module Status ← `COMPONENT_STATUS` (label, tier, completion, evidence)
- Voice Launch Gates ← `VOICE_LAUNCH_GATES`
- Series A Readiness Gates ← `SERIES_A_GAPS`
- Stephanie Matrix Truth Register ← `CLAIM_NORMALIZATIONS`

Later phases (not first): Approval Log push (Stephanie proposals + Cyborg
human-required actions → `Needs Michael` rows) and Workflow/Jobs sync.

## Out of scope for this repo / session

The report's 30–90 day items are infra/business workstreams, not changes here:
voice latency remediation (msgpack WS, Canvas2D/rAF, FFTW, libopus SIMD,
uvloop/GC), load tests (25→50→100 session), ERPNext GC-vs-platform P&L split,
CPA review, data room. **Replit:** app creation is blocked on `401 —
reauthentication`; reconnect Replit authorization before any push there.
