# Jobs Domain

The Jobs domain owns the full execution lifecycle of a NoblePort job once an
estimate has been won and a deposit is in motion. It is the connective tissue
between sales (Estimates), field operations (Construction), and finance
(Invoices/Payments). Once a job is kicked off, every progress update, change
order, at-risk flag, and final closeout flows through this domain.

This domain reuses the existing `Job`, `ChangeOrder`, and `Estimate` models and
exposes a single `JobsService` plus a FastAPI router for HTTP access.

## Capabilities

- Kick off a job once the deposit gate has cleared (assign PM/crew, set start date)
- Update percent-complete progress and recompute completion forecasts
- Add change orders (AWOs) directly against an active job
- Compute live profitability (contract value vs. costs vs. AWOs)
- Flag a job as at-risk with a reason so it surfaces in ops briefings
- List active jobs (with status/filter scoping) and per-job health snapshots
- Close out a completed job and queue the maintenance contract hand-off
