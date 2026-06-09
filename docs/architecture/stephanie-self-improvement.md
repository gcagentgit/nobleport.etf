# Stephanie.ai — Recursive Self-Improvement

Stephanie improves her own decision-making by learning from the realized
outcomes of her past decisions. Each accepted change produces a new policy
**generation** that the next cycle builds on, so gains compound over time —
that is what makes the loop *recursive*. It is also deliberately **bounded and
human-gated**: this is controlled operations tuning, not an open-ended
self-modifying system.

## The control rule

> **AI observes → drafts → scores → recommends → authorized human approves →
> system logs → system learns.**

Stephanie.ai is **not AGI and not an autonomous executive signer.** She does
not autonomously change code, policies, contracts, or pricing, and she does
not handle financial transactions, legal obligations, or external
communications without a defined human control checkpoint. The loop *proposes*;
a human *deploys*.

## Why this exists

Stephanie's logic used to carry hardcoded literals — `estimated_value >= 100_000`
for fast-tracking, `days_stale > 14` for critical severity, health-score
weights, and so on. Those numbers were guesses frozen at write time. The
self-improvement loop turns them into a versioned, tunable policy and lets
Stephanie *recommend* adjustments based on what actually happened to the leads
and jobs she decided on — for a human to approve.

## The controlled loop

```
observe → normalize → score → compare → diagnose → propose → [HUMAN APPROVES]
   ^                                                                   |
   |                                                                deploy
   |                                                                   |
   +---------------- lock ←── monitor (verify on fresh outcomes) ──────+
                       └──── rollback (auto, if it regressed) ─────────+
```

| Stage | What happens | Code |
| --- | --- | --- |
| **observe** | Ingest decision outcomes — what Stephanie decided and what actually happened (lead converted? for how much?). | `learn_from_lead_outcomes`, `record_outcomes` |
| **score / compare** | Counterfactual replay: re-derive what a candidate policy *would* have decided on the same history, score it against realized outcomes. | `intake_objective`, `score` |
| **diagnose** | Explain *why* the current policy under-performs, with evidence (converted leads not fast-tracked; fast-tracked leads that never converted). | `diagnose` → `Diagnosis` |
| **propose** | Coordinate-descent over tunable parameters; each move capped at its `max_step` and clamped to hard bounds. Must beat the current policy by `MIN_IMPROVEMENT`. | `propose` |
| **govern** | Control-mode + risk-tier gate + circuit breaker; write every step to the AuditBeacon chain. | `_govern`, `CircuitBreaker` |
| **deploy** | Human approves → bump the generation, version the policy as **provisional**. | `approve`, `apply` |
| **monitor → lock / rollback** | Verify the provisional change still beats its parent on *fresh* outcomes: lock it if it holds, auto-roll back if it regressed. | `verify` → `VerificationReport` |

## Safety model

The loop cannot run away, every change is human-approved by default, and every
applied change is reversible, monitored, and audited:

1. **Fail-closed by default.** The control mode starts at `FAIL_CLOSED`: the
   loop only ever *recommends*, and a human approves every deploy.
   `OPERATIONAL_AUTO` is an explicit, audited opt-in that lets **LOW-risk
   operational** tuning (e.g. ops-brief severity cutoffs) auto-apply — it never
   relaxes MEDIUM/HIGH gating.
2. **Hard bounds + step caps.** Every parameter in `PARAMETER_SPECS` has a
   `minimum`, `maximum`, and `max_step`. The loop physically cannot drive a
   parameter out of range or make a large uncontrolled jump in one generation.
3. **Proven improvement only.** A change must improve a concrete objective on
   historical outcomes by at least `MIN_IMPROVEMENT`. No improvement, no
   proposal.
4. **Risk tiers, mirroring Cyborg.** Even in `OPERATIONAL_AUTO`, `MEDIUM`
   requires strong improvement *and* high confidence, and `HIGH` (e.g.
   `high_value_threshold`, which drives senior-estimator and site-visit spend)
   **always** requires human approval.
5. **Monitor → lock / rollback.** An applied generation is `PROVISIONAL` until
   `verify` proves it still beats its parent on *fresh* outcomes. If it
   regresses it is auto-rolled-back and the miss is fed to the circuit breaker —
   stopping the loop from compounding changes that only looked good in-sample.
6. **Circuit breaker.** Trips after consecutive verification regressions,
   blocking auto-apply until a human resets it — guarding against drift and
   reward-hacking.
7. **Immutable audit + rollback.** Generations form a parent-linked chain;
   each governed action is recorded on the AuditBeacon hash chain, and any
   generation can be restored with `rollback`.

## The objective

The default objective optimizes **intake-routing value capture**:

```
reward = converted value captured on fast-tracked leads
       - fast_track_cost per fast-tracked lead
       - 0.25 * won_value for converted leads that were NOT prioritized
```

This makes `high_value_threshold` a real trade-off: lowering it captures more
conversions but spends more on fast-tracking; raising it saves spend but risks
missing winners. The objective is pluggable (`ObjectiveFn`) so other decision
domains can be optimized later.

## API

Mounted at `/api/v1/stephanie/improvement` (see `backend/api/self_improvement.py`):

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/control-rule` | The operating model + live control mode (fail-closed?) |
| GET | `/truth` | Truth layer — component statuses, flywheels, priority phases |
| GET | `/policy` | Current tuned policy + generation |
| GET | `/state` | Full loop state (policy, control mode, lock state, breaker) |
| GET | `/history` | The recursive chain of policy generations |
| GET | `/proposals` | Proposals awaiting human approval |
| POST | `/cycle?auto_apply=&lookback_days=` | Run one improvement cycle (recommend) |
| POST | `/proposals/{id}/approve` | Approve + apply a proposal (human deploy) |
| POST | `/proposals/{id}/reject` | Reject a proposal |
| POST | `/verify` | Monitor → lock the provisional generation or auto-roll-back |
| POST | `/control-mode` | Switch fail-closed ↔ operational-auto (audited) |
| POST | `/rollback` | Restore a prior generation |
| POST | `/breaker/reset` | Clear an open circuit breaker |

The same cycle is reachable through the agent mesh as the
`run_self_improvement` event, which is audited automatically by the
orchestrator.

## Truth layer & flywheels

The control rule depends on an honest status picture, so the loop ships with a
**truth registry** (`backend/agents/truth_registry.py`): every component carries
a `LIVE` / `STAGED` / `SIMULATED` / `TARGET` / `PENDING` label with ground
truth, and a `label_claim` / `reconcile` helper downgrades unproven `LIVE`
claims by default. The registry also encodes the **12 improvement flywheels**
(lead→estimate, estimate→actual, proposal→signed, permit-packet→AHJ, …) and the
revenue-first priority phases. Honest read: **construction operations is the
live, monetizable engine; voice/avatar, token, governance, and municipal
automation stay STAGED until evidence, audit, and production gates close.**

## Where it lives

- `backend/agents/stephanie_policy.py` — tunable policy, bounds, risk tiers, lock states, versions
- `backend/agents/self_improvement.py` — the loop engine, objective, diagnose, monitor/verify, circuit breaker
- `backend/agents/truth_registry.py` — control rule, truth-layer statuses, flywheels, truth-labeling
- `backend/agents/stephanie.py` — reads parameters from the live policy; feeds real lead outcomes into the loop
- `backend/api/self_improvement.py` — Mission Control API
- `backend/tests/test_stephanie_self_improvement.py` — bounds, control rule, governance, diagnose, monitor/lock/rollback, breaker, truth registry
