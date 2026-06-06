# Permits Domain

The Permits domain handles the regulated paperwork lifecycle of every NoblePort
job: submitting building/electrical/plumbing/mechanical permits to the
appropriate Authority Having Jurisdiction (AHJ), tracking review cycles and
corrections, recording issuance, and scheduling/recording all required
inspections. This is the domain that prevents jobs from running ahead of
their legal authorization to build.

This domain reuses the existing `Permit`, `Inspection`, and `Project` models.
There are no new tables.

## Capabilities

- Submit a new permit application (creates Permit + transitions to submitted)
- Record correction cycles from the AHJ and increment the corrections counter
- Record issuance with permit number, issued-at, and expiration date
- Schedule and record results of every required inspection (pass/fail)
- List all open permits, optionally scoped by AHJ
- Pull pending/upcoming inspections within a configurable window
