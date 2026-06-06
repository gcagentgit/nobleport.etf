# Workflows Domain

The workflows domain is the orchestration heart of NoblePort OS. A **workflow** is a
named, versioned, multi-step sequence of actions triggered by a business event
(for example `estimate_won`, `deposit_paid`, `permit_approved`, `job_completed`).
Templates declare *what should happen and in what order*; instances are concrete
runs against a specific entity (a lead, an estimate, a job, a permit). Each step
is dispatched by `action_type` — route to a specific AgentMesh agent, create a
task, send a communication, update an entity, wait, conditionally branch, call
an external API, request human approval, or record a trust event. Steps support
dependency ordering, conditions, timeouts, retries, and failure policies
(`fail`, `skip`, `retry`, `escalate`).

Workflows are **not** follow-ups. A follow-up is a customer-facing communication
cadence (text/email reminders, drip nudges, "are you ready to sign?" pokes) and
lives in `domains/follow_ups`. A workflow is an *internal business process* that
can span multiple agents and multiple domains — for example, "Lead Intake to
Estimate" hops from intake → Stephanie qualification → estimator assignment →
proposal send → follow-up creation. Workflows can *invoke* follow-ups as one of
their steps; the inverse is rarely true.

Every workflow run integrates with the existing kernel. `route_to_agent` steps
go through `backend.agents.orchestrator.AgentMesh.route_event`, which means every
routed event is *already* persisted in the hash-chained ledger. The
`record_trust_event` action provides a direct path to `AuditBeacon` for any step
that needs an explicit, named record-of-trust (deposit captured, contract
counter-signed, permit issued). Instance lifecycle transitions (started, paused,
resumed, cancelled, failed) are themselves recorded as trust events, so the
ledger is the source of truth for "did this process actually happen?"

## Capabilities

- Register, version, and deactivate workflow templates
- Trigger workflows from any event with payload-based filter conditions
- Execute multi-step processes with dependency ordering and branching
- Dispatch nine action types (route, task, comms, update, wait, branch, api, approval, trust)
- Pause, resume, and cancel running instances
- Track per-step execution history (status, attempts, output, errors)
- Surface health metrics: running / completed / failed / p50 duration / success rate
- Seed canonical templates covering the core revenue lifecycle
