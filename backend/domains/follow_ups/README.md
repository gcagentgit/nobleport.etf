# Follow-Ups Domain

The follow-ups domain owns automated, multi-step follow-up sequences and the
scheduled reminders that fire from them. A sequence is a reusable template of
steps (e.g. day 0 email -> day 3 SMS -> day 7 phone call); an instance is a
specific run of that sequence against a contact, lead, or active job.

The domain is responsible for keeping each instance moving on its schedule,
pausing or cancelling when a response is received, and exposing the queue of
steps that are due to be sent.

## Capabilities

- Define reusable follow-up sequences with ordered, delayed, channel-specific steps
- Start a sequence instance against a contact / lead / job
- Pause, cancel, or record a response on an instance
- Process all steps due for delivery (cron / worker entry point)
- Inspect upcoming follow-up workload (next 24 hours of due steps)
