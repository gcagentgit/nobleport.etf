---
name: change-orders
description: Controls project scope by drafting change orders with cost impacts, approval routing, and an append-only audit trail. Use when a job's scope changes and needs a priced change order, when a change needs approval routing, or when an auditable scope-change record is required. Change orders above the declared threshold are never auto-approved — they escalate to a human, and the audit trail is tamper-evident.
---

# Change Order Skill

**Tier 2 — NoblePort Operations · Status: LIVE (draft) / human-approval gate · gcagent module: `construction_operations`**

Keeps scope under control. Every change to a signed job becomes a priced,
routed, audited change order — never a verbal handshake that erodes margin.

## When to use

- A job's **scope changes** and needs a documented, priced change order.
- A change needs **approval routing** to the right human.
- An **audit trail** of scope changes is required for a job or dispute.

## Inputs

- Original contract / estimate (baseline scope and total).
- The requested change (added/removed scope, with measurements).
- Approval policy and the auto-approve threshold.

## Outputs

- **Change order** — delta scope, priced via the `estimator` skill.
- **Cost impact** — effect on contract total and on margin.
- **Approval routing** — to the correct approver per policy.
- **Audit trail** — append-only, hash-chained scope-change record.

## Workflow

1. Capture the change against the baseline scope.
2. Price the delta through `estimator`; compute the new contract total and margin.
3. Compare the change value to the auto-approve threshold.
4. Below threshold → route for standard approval; **above → escalate to a human.**
5. Record the decision in the append-only, hash-chained audit trail.

## Knowledge & data sources

- `construction_operations` change-order triage and thresholds.
- `estimator` for delta pricing; MA HIC requires written, signed change orders.
- Audit pattern mirrors the Stephanie gate's SHA-256 hash-chained ledger and the
  on-chain `HumanApprovalGateway.sol`.

## Safety & approval gates

- **Never auto-approve a change order above the declared threshold** — it escalates.
- Change orders are **draft until signed** by the customer (MA HIC: in writing).
- The audit trail is **append-only**; corrections are new, paired records — never edits.
- Cost/margin impact is always shown; scope never changes silently.

## Success criteria

- Every change order reconciles the new total to baseline plus the priced delta.
- Approval state and approver are recorded for every change.
- The audit chain verifies (tamper-evident).

## Failure modes

- `change_order_approval_bypass` — an over-threshold change slipping through.
- `unpriced_scope_creep` — scope added without a cost impact.
- `audit_trail_edit` — mutating a past record instead of appending a correction.
