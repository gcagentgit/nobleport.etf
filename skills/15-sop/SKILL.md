---
name: sop
description: Produces and maintains standard operating procedures — process documentation, training guides, and checklists — for NoblePort's repeatable workflows. Use when a user needs to document a process, build a training guide, or turn a workflow into a checklist. SOPs describe the approved process; changes are versioned and reviewed before they become canonical.
---

# SOP Skill

**Tier 3 — Growth Engine · Status: LIVE (internal) · gcagent module: `reporting_automation`**

Captures how NoblePort does things so the operation scales beyond any one
person's memory — the connective tissue under every other skill.

## When to use

- A repeatable workflow needs to become a **documented SOP**.
- New staff/subs need a **training guide**.
- A process needs a **checklist** for consistent field or office execution.

## Inputs

- The workflow to document (steps, roles, tools, decision points).
- Existing SOPs and the documentation style guide.
- Approval and review policy for canonical procedures.

## Outputs

- **Process documentation** — step-by-step SOPs with roles and tools.
- **Training guides** — onboarding-oriented walkthroughs.
- **Checklists** — execution-ready, single-pass lists.

## Workflow

1. Capture the real process, including roles, tools, and decision points.
2. Draft the SOP / training guide / checklist in the house format.
3. Cross-reference related skills (e.g. `change-orders`, `payment-node`) so the
   SOP matches the actual approval gates.
4. Version the document; submit material changes for review before they go canonical.

## Knowledge & data sources

- Existing NoblePort workflows and the other skills in this library.
- The documentation style guide and the truth-tag discipline.

## Safety & approval gates

- An SOP describes the **approved** process — it must not document a shortcut
  around a safety or approval gate (e.g. unapproved disbursements).
- Material changes are **versioned and reviewed** before becoming canonical.
- SOPs reference, and stay consistent with, the human-approval gates in the
  skills they cover.

## Success criteria

- SOPs are followable by someone new without tribal knowledge.
- Checklists are single-pass and unambiguous.
- Documented approval steps match the real gates in the referenced skills.

## Failure modes

- `sop_documents_a_gate_bypass` — codifying a workaround around an approval gate.
- `stale_sop` — a procedure that no longer matches the live workflow.
- `unversioned_change` — a canonical edit with no review or version history.
