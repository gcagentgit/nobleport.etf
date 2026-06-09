# Stephanie.ai — Recursive Self-Improvement

Stephanie improves her own decision-making by learning from the realized
outcomes of her past decisions. Each accepted change produces a new policy
**generation** that the next cycle builds on, so gains compound over time —
that is what makes the loop *recursive*. It is also deliberately **bounded**:
this is operations tuning under governance, not an open-ended self-modifying
system.

## Why this exists

Stephanie's logic used to carry hardcoded literals — `estimated_value >= 100_000`
for fast-tracking, `days_stale > 14` for critical severity, health-score
weights, and so on. Those numbers were guesses frozen at write time. The
self-improvement loop turns them into a versioned, tunable policy and lets
Stephanie adjust them based on what actually happened to the leads and jobs
she decided on.

## The loop

```
observe  ->  propose  ->  evaluate  ->  govern  ->  apply / queue
   ^                                                       |
   +------------------- next generation -------------------+
```

| Stage | What happens | Code |
| --- | --- | --- |
| **observe** | Ingest decision outcomes — what Stephanie decided and what actually happened (lead converted? for how much?). | `learn_from_lead_outcomes`, `record_outcomes` |
| **propose** | Coordinate-descent over tunable parameters; each move capped at its `max_step` and clamped to hard bounds. | `propose` |
| **evaluate** | Counterfactual replay: re-derive what the candidate policy *would* have decided on the same history, score it against realized outcomes. A change must beat the current policy by `MIN_IMPROVEMENT` to qualify. | `intake_objective`, `score` |
| **govern** | Risk-tier gate + circuit breaker; write every step to the AuditBeacon chain. | `_govern`, `CircuitBreaker` |
| **apply** | Bump the generation, version the policy, keep full history for rollback. | `apply`, `rollback` |

## Safety model

The loop cannot run away, and every change is reversible and audited:

1. **Hard bounds + step caps.** Every parameter in `PARAMETER_SPECS` has a
   `minimum`, `maximum`, and `max_step`. The loop physically cannot drive a
   parameter out of range or make a large uncontrolled jump in one generation.
2. **Proven improvement only.** A change must improve a concrete objective on
   historical outcomes by at least `MIN_IMPROVEMENT`. No improvement, no
   proposal.
3. **Risk tiers, mirroring Cyborg.** `LOW`-tier parameters may be auto-applied
   when improvement is proven. `MEDIUM` requires strong improvement *and* high
   confidence. `HIGH` (e.g. `high_value_threshold`, which drives senior-estimator
   and site-visit spend) **always** requires human approval.
4. **Circuit breaker.** Trips after consecutive regressions, blocking
   auto-apply until a human resets it — guarding against drift and
   reward-hacking where proxy-objective gains don't hold on fresh data.
5. **Dry-run by default.** `run_cycle` only commits when `auto_apply` is set
   AND governance returned `AUTO_APPLY` AND the breaker is closed. Everything
   else is queued for a human.
6. **Immutable audit + rollback.** Generations form a parent-linked chain;
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
| GET | `/policy` | Current tuned policy + generation |
| GET | `/state` | Full loop state (policy, breaker, pending proposals) |
| GET | `/history` | The recursive chain of policy generations |
| GET | `/proposals` | Proposals awaiting human approval |
| POST | `/cycle?auto_apply=&lookback_days=` | Run one improvement cycle |
| POST | `/proposals/{id}/approve` | Approve + apply a proposal |
| POST | `/proposals/{id}/reject` | Reject a proposal |
| POST | `/rollback` | Restore a prior generation |
| POST | `/breaker/reset` | Clear an open circuit breaker |

The same cycle is reachable through the agent mesh as the
`run_self_improvement` event, which is audited automatically by the
orchestrator.

## Where it lives

- `backend/agents/stephanie_policy.py` — tunable policy, bounds, risk tiers, versions
- `backend/agents/self_improvement.py` — the loop engine, objective, circuit breaker
- `backend/agents/stephanie.py` — reads parameters from the live policy; feeds real lead outcomes into the loop
- `backend/api/self_improvement.py` — Mission Control API
- `backend/tests/test_stephanie_self_improvement.py` — bounds, governance, breaker, generations, rollback
