# Intake Domain

The intake domain owns the very first interaction NoblePort has with a prospective
customer. It accepts inbound leads from web forms, phone calls, email parsers, and
referral partners, normalizes the payload into a `Lead`, applies a lightweight
qualification pass, and routes the lead to either fast-track sales or a longer
nurture sequence.

Intake intentionally does not own pipeline management beyond first qualification;
once a lead is qualified and assigned, the `leads/` domain takes over.

## Capabilities

- Capture leads from any inbound channel (web, phone, email, referral, walk-in)
- Score & qualify based on signals (budget, timeline, scope, location)
- Route fast-track opportunities into a sales rep's queue
- Assign leads to a specific owner with audit trail
- Summarize intake volume by source over the last 30 days
