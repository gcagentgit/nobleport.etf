# Leads Domain

The leads domain manages a qualified lead's full journey through the sales
pipeline. Where `intake/` does first-touch capture and triage, `leads/` owns
ongoing scoring, stage progression, owner reassignment, archival of dead
opportunities, and roll-up funnel reporting that feeds the sales dashboard.

This domain operates on the existing `Lead` model and does not introduce new
persistence — its job is operational logic over leads that already exist.

## Capabilities

- Recompute lead scores from signal updates (touches, recency, fit)
- Advance leads through the funnel (new -> contacted -> qualified -> proposal -> won/lost)
- Reassign owners with reason for audit
- Archive stale or dead leads
- Provide a funnel snapshot (counts per stage + stage-to-stage conversion %)
- List the active pipeline filtered by owner / stage
