/**
 * Nemoclaw v1 — Proposal Lifecycle Manager
 *
 * Manages proposal state transitions (§8), approval recording,
 * and RWA-specific checks (§13).
 */

import { randomUUID } from 'crypto';
import {
  ActionClass,
  ApprovalRecord,
  Proposal,
  ProposalState,
  Role,
  DataSource,
  SimulationResult,
  ValidationResult,
} from './types';
import {
  canCreateProposal,
  checkSeparationOfDuties,
  resolveApprovalThreshold,
  validateRoleForAction,
} from './policy';

// ─── Valid State Transitions (§8.1) ────────────────────────────────

const VALID_TRANSITIONS: Record<ProposalState, ProposalState[]> = {
  [ProposalState.Draft]: [ProposalState.Validated, ProposalState.Rejected],
  [ProposalState.Validated]: [ProposalState.QueuedForApproval, ProposalState.Rejected],
  [ProposalState.QueuedForApproval]: [
    ProposalState.Approved,
    ProposalState.Rejected,
    ProposalState.Expired,
  ],
  [ProposalState.Approved]: [
    ProposalState.PreparedForExecution,
    ProposalState.Expired,
    ProposalState.Halted,
  ],
  [ProposalState.Rejected]: [],
  [ProposalState.Expired]: [],
  [ProposalState.PreparedForExecution]: [
    ProposalState.Executed,
    ProposalState.Failed,
    ProposalState.Halted,
  ],
  [ProposalState.Executed]: [ProposalState.Reconciled, ProposalState.Failed],
  [ProposalState.Reconciled]: [],
  [ProposalState.Failed]: [ProposalState.Halted],
  [ProposalState.Halted]: [],
};

// ─── Proposal Manager ─────────────────────────────────────────────

export class ProposalManager {
  private proposals = new Map<string, Proposal>();

  /** Create a new proposal in Draft state */
  createProposal(params: {
    creatorService: string;
    creatorRole: Role;
    actionClass: ActionClass;
    assetOrWorkflowTarget: string;
    amountOrEffectSize: number;
    amountUsdEquivalent: number;
    rationale: string;
    sourceSet: DataSource[];
    payloadHash: string;
    expiryTimestamp: number;
    linkedAssetId?: string;
    documentComplete?: boolean;
  }): { proposal: Proposal | null; error?: string } {
    // §6.2: validate role
    const roleCheck = validateRoleForAction(params.creatorRole, 'create_proposal');
    if (!roleCheck.allowed) {
      return { proposal: null, error: roleCheck.reason };
    }

    const now = Date.now();
    const proposal: Proposal = {
      proposalId: randomUUID(),
      correlationId: randomUUID(),
      creatorService: params.creatorService,
      creatorRole: params.creatorRole,
      actionClass: params.actionClass,
      assetOrWorkflowTarget: params.assetOrWorkflowTarget,
      amountOrEffectSize: params.amountOrEffectSize,
      amountUsdEquivalent: params.amountUsdEquivalent,
      rationale: params.rationale,
      sourceSet: params.sourceSet,
      validationResult: null,
      simulationResult: null,
      riskScore: 0,
      requiredApprovals: resolveApprovalThreshold(
        params.actionClass,
        params.amountUsdEquivalent,
      ),
      approvals: [],
      payloadHash: params.payloadHash,
      expiryTimestamp: params.expiryTimestamp,
      state: ProposalState.Draft,
      createdAt: now,
      updatedAt: now,
      linkedAssetId: params.linkedAssetId,
      documentComplete: params.documentComplete,
    };

    this.proposals.set(proposal.proposalId, proposal);
    return { proposal };
  }

  /** Transition proposal to a new state */
  transition(
    proposalId: string,
    newState: ProposalState,
  ): { success: boolean; error?: string } {
    const proposal = this.proposals.get(proposalId);
    if (!proposal) {
      return { success: false, error: 'Proposal not found' };
    }

    const allowed = VALID_TRANSITIONS[proposal.state];
    if (!allowed.includes(newState)) {
      return {
        success: false,
        error: `Cannot transition from ${proposal.state} to ${newState}`,
      };
    }

    proposal.state = newState;
    proposal.updatedAt = Date.now();
    return { success: true };
  }

  /** Attach validation result and advance to Validated if passed */
  setValidationResult(
    proposalId: string,
    result: ValidationResult,
  ): { success: boolean; error?: string } {
    const proposal = this.proposals.get(proposalId);
    if (!proposal) return { success: false, error: 'Proposal not found' };
    if (proposal.state !== ProposalState.Draft) {
      return { success: false, error: 'Proposal must be in Draft state for validation' };
    }

    proposal.validationResult = result;
    proposal.updatedAt = Date.now();

    if (result.passed) {
      return this.transition(proposalId, ProposalState.Validated);
    }
    return this.transition(proposalId, ProposalState.Rejected);
  }

  /** Attach simulation result */
  setSimulationResult(
    proposalId: string,
    result: SimulationResult,
  ): { success: boolean; error?: string } {
    const proposal = this.proposals.get(proposalId);
    if (!proposal) return { success: false, error: 'Proposal not found' };

    proposal.simulationResult = result;
    proposal.riskScore = result.warnings.length * 10; // simple risk heuristic
    proposal.updatedAt = Date.now();
    return { success: true };
  }

  /** Queue a validated proposal for approval */
  queueForApproval(proposalId: string): { success: boolean; error?: string } {
    return this.transition(proposalId, ProposalState.QueuedForApproval);
  }

  /** Record an approval on a proposal */
  addApproval(
    proposalId: string,
    approval: ApprovalRecord,
  ): { success: boolean; error?: string } {
    const proposal = this.proposals.get(proposalId);
    if (!proposal) return { success: false, error: 'Proposal not found' };
    if (proposal.state !== ProposalState.QueuedForApproval) {
      return { success: false, error: 'Proposal must be queued for approval' };
    }

    // §6.2: validate approver role
    const roleCheck = validateRoleForAction(approval.role, 'approve');
    if (!roleCheck.allowed) {
      return { success: false, error: roleCheck.reason };
    }

    // §6.3: separation of duties
    const dutyCheck = checkSeparationOfDuties(proposal, approval.approverId);
    if (!dutyCheck.passed) {
      return { success: false, error: dutyCheck.reason };
    }

    // Check for duplicate approver
    if (proposal.approvals.some(a => a.approverId === approval.approverId)) {
      return { success: false, error: 'Approver has already approved this proposal' };
    }

    proposal.approvals.push(approval);
    proposal.updatedAt = Date.now();
    return { success: true };
  }

  /** Mark proposal as approved (after verifying all approvals met) */
  approve(proposalId: string, now: number): { success: boolean; error?: string } {
    const proposal = this.proposals.get(proposalId);
    if (!proposal) return { success: false, error: 'Proposal not found' };

    // RWA-specific checks (§13)
    if (proposal.actionClass === ActionClass.E_FinalRWA) {
      const rwaCheck = this.checkRWARequirements(proposal);
      if (!rwaCheck.passed) {
        return { success: false, error: rwaCheck.reason };
      }
    }

    return this.transition(proposalId, ProposalState.Approved);
  }

  /** Prepare an approved proposal for execution */
  prepareForExecution(proposalId: string): { success: boolean; error?: string } {
    return this.transition(proposalId, ProposalState.PreparedForExecution);
  }

  /** Mark proposal as executed */
  markExecuted(proposalId: string): { success: boolean; error?: string } {
    return this.transition(proposalId, ProposalState.Executed);
  }

  /** Mark proposal as reconciled */
  markReconciled(proposalId: string): { success: boolean; error?: string } {
    return this.transition(proposalId, ProposalState.Reconciled);
  }

  /** Mark proposal as failed */
  markFailed(proposalId: string): { success: boolean; error?: string } {
    return this.transition(proposalId, ProposalState.Failed);
  }

  /** Halt a proposal */
  halt(proposalId: string): { success: boolean; error?: string } {
    return this.transition(proposalId, ProposalState.Halted);
  }

  /** Expire proposals past their expiry timestamp */
  expireStale(now: number): string[] {
    const expired: string[] = [];
    for (const [id, proposal] of this.proposals) {
      if (
        proposal.expiryTimestamp <= now &&
        ![
          ProposalState.Executed,
          ProposalState.Reconciled,
          ProposalState.Rejected,
          ProposalState.Expired,
          ProposalState.Failed,
          ProposalState.Halted,
        ].includes(proposal.state)
      ) {
        proposal.state = ProposalState.Expired;
        proposal.updatedAt = now;
        expired.push(id);
      }
    }
    return expired;
  }

  /** Get a proposal by ID */
  get(proposalId: string): Proposal | undefined {
    return this.proposals.get(proposalId);
  }

  /** List proposals by state */
  listByState(state: ProposalState): Proposal[] {
    return Array.from(this.proposals.values()).filter(p => p.state === state);
  }

  // ─── RWA Checks (§13) ───────────────────────────────────────────

  private checkRWARequirements(proposal: Proposal): { passed: boolean; reason: string } {
    // §13.1: linked asset ID verification
    if (!proposal.linkedAssetId) {
      return { passed: false, reason: 'RWA execution requires linked asset ID' };
    }

    // §13.1: document/state completeness
    if (!proposal.documentComplete) {
      return { passed: false, reason: 'RWA execution requires document completeness' };
    }

    // §13.1: double-approval minimum
    if (proposal.approvals.length < 2) {
      return { passed: false, reason: 'RWA execution requires minimum 2 approvals' };
    }

    return { passed: true, reason: 'RWA requirements met' };
  }
}
