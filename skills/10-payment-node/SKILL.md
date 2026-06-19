---
name: payment-node
description: Applies financial controls to construction payments — draw schedules, deposit validation, retention tracking, and compliance review — with human approval required for every disbursement. Use when a user needs a draw schedule, a deposit checked against Massachusetts HIC limits, retention tracked, or a payment compliance review. The agent never moves money: it drafts and validates, humans approve via the HumanApprovalGateway.
---

# Payment Node Skill

**Tier 2 — NoblePort Operations · Status: STAGED (`treasury_workflows`) · Surface: NoblePort Payment Node**

The financial-controls layer of the revenue spine (**Invoice → Closeout**). It
structures and checks money movement; it never executes it autonomously.

## When to use

- A job needs a **draw schedule** tied to build milestones.
- A **deposit** must be validated against Massachusetts HIC limits.
- **Retention** needs tracking across draws.
- A payment needs a **compliance review** before a human releases it.

## Inputs

- Contract total and payment schedule from `estimator`.
- Build milestone state from `project-manager`.
- Deposit/draw policy and MA HIC constraints.
- Stripe/QuickBooks records (`treasury_workflows`, STAGED).

## Outputs

- **Draw schedule** — milestone-linked disbursement plan.
- **Deposit validation** — pass/fail against the statutory cap.
- **Retention tracking** — withheld amounts across draws.
- **Compliance review** — flags before a human approves a disbursement.

## Workflow

1. Build the draw schedule from contract total and build milestones.
2. Validate the deposit against the MA HIC cap (≤ 1/3 of total, or special-order
   material cost, whichever is greater).
3. Track retention withheld and released per draw.
4. Run the compliance review; surface every flag.
5. Submit for human approval through the gateway. **The agent never disburses.**

## Knowledge & data sources

- Massachusetts Home Improvement Contractor law (M.G.L. c.142A) deposit limits.
- `treasury_workflows` (STAGED): Stripe invoicing, deposit logging, tracking.
- `HumanApprovalGateway.sol` and the Stephanie gate (> $5,000 escalates).

## Safety & approval gates

- **Every disbursement requires human approval.** This skill drafts and validates;
  it does not move money.
- Deposits above the MA HIC statutory cap **fail validation** — no exceptions.
- Amounts over **$5,000** escalate per the governance gate.
- Records are written before any notification fires; corrections are versioned.

## Success criteria

- Draw schedules reconcile to the contract total and the build milestones.
- Deposit validation is correct against the statutory cap.
- Every disbursement carries a matched human-approval record.

## Failure modes

- `autonomous_disbursement` — moving money without an approval record.
- `deposit_over_statutory_cap` — passing a deposit that exceeds the HIC limit.
- `retention_drift` — withheld/released retention not reconciling across draws.
