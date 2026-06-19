---
name: project-manager
description: Runs job execution for active construction projects — daily logs, scheduling, material tracking, subcontractor coordination, and inspection scheduling — with Buildertrend as the system of record. Use when a user needs to log field activity, build or adjust a schedule, track materials, coordinate subs, or line up inspections. Buildertrend is source of truth; conflicts escalate rather than overwrite.
---

# Project Manager Skill

**Tier 1 — Core Construction · Status: LIVE (`crew_task_routing`); scheduling STAGED (`calendar_scheduling`) · gcagent module: `construction_operations`**

Coordinates the **Build** phase of the revenue spine: daily logs, schedules,
materials, subs, and inspections, keeping the office and the field in sync.

## When to use

- A field update needs to become a **daily log** entry.
- A job **schedule** needs to be built or adjusted around dependencies.
- **Materials** need tracking against the estimate's takeoff.
- **Subcontractors** need coordination (scope, dates, submittals).
- An **inspection** needs scheduling with the AHJ.

## Inputs

- Buildertrend job state and events (system of record).
- Field logs, photos, and voice updates (`voice_intake`, LIVE).
- Subcontractor submittals and availability.
- The job's estimate/takeoff and permit milestones.

## Outputs

- **Daily logs** — dated, attributed field records.
- **Schedule updates** — task sequence with dependencies and durations.
- **Material tracking** — ordered vs. delivered vs. installed against takeoff.
- **Sub coordination** — assignments with scope and dates.
- **Inspection scheduling** — requests tied to the right build milestone.

## Workflow

1. Ingest field updates and reconcile against Buildertrend job state.
2. Update or sequence schedule tasks; surface dependency conflicts.
3. Track material status against the estimate takeoff; flag shortfalls.
4. Assign and confirm subcontractor scope and dates.
5. Schedule inspections at the correct milestone.
6. On any office/field conflict, **escalate — do not overwrite Buildertrend.**

## Knowledge & data sources

- Buildertrend (system of record) via `backend/integrations/buildertrend_client.py`
  and `backend/services/sync_engine.py`.
- `crew_task_routing` (LIVE) for routing tasks out of intake.
- `calendar_scheduling` (STAGED, Google Calendar) for job scheduling.

## Safety & approval gates

- **Buildertrend is the source of truth.** Conflicts escalate; they never silently
  overwrite the record.
- Field-originated edits require office confirmation before downstream sync.
- Inspection requests are drafted; the human confirms with the AHJ.
- No change-order approval here — that routes to the `change-orders` skill.

## Success criteria

- Backend job state matches Buildertrend within the sync SLA.
- Every schedule task has a declared dependency and owner.
- Each escalation has a named owner and a resolution path.

## Failure modes

- `silent_sync_divergence` — backend and Buildertrend drift apart unnoticed.
- `schedule_flap_from_duplicate_events` — duplicate events thrash the schedule.
- `material_shortfall_missed` — installed-vs-ordered gap not surfaced in time.
