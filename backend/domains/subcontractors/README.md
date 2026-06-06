# Subcontractors Domain

The Subcontractors domain owns the NoblePort sub directory and every workflow
that touches a sub: bid intake, bid awarding, job assignment, insurance
compliance (W-9, GL/WC carrier + expiration), and payment tracking with lien
waivers. This is also the source of truth for "who is preferred for which
trade" and for flagging subs whose insurance has lapsed before they roll onto
a site.

Unlike the other domains, Subcontractors introduces **new tables** because
none of the existing models cover sub-side data. See `models.py` for the
SQLAlchemy schema: `Subcontractor`, `SubcontractorBid`,
`SubcontractorAssignment`, `SubcontractorPayment`.

## Capabilities

- Maintain a directory of subs with trades, license, insurance, W-9, rating
- Record and update insurance details; flag lapsed coverage
- Surface subs whose insurance expires within a configurable window
- Capture incoming bids on a job; award one (auto-reject competing bids)
- Assign a sub to a job under a scope + contract amount
- Record payments against an assignment with lien-waiver tracking
- Look up preferred subs for a given trade
