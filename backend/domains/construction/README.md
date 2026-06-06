# Construction Domain

The Construction domain is the field-operations layer of NoblePort OS. Where
the Jobs domain tracks contractual execution, Construction tracks what is
actually happening on the dirt today: which crew is on which site, what
materials arrived, what was built, what got hit by weather, and any safety
incidents that occurred. Daily logs flow into this domain as the canonical
record of activity, and downstream consumers (ops briefings, change-order
suggestions, owner reports) read from here.

This domain reuses the existing `DailyLog`, `ScheduleItem`, `Project`, and
`Job` models. There are no new tables.

## Capabilities

- Submit a structured daily log for any project (weather, crew, work, safety)
- Read live field status for a job (most recent log, in-progress tasks, weather)
- Record a material delivery against an active job
- Report a safety incident and flag the job/log accordingly
- Roll up "what is active today" across every running site
- Show the current crew distribution by site/job
