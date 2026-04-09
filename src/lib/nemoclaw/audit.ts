/**
 * Nemoclaw v1 — Audit Trail
 *
 * Implements append-only audit records (§14), snapshot points,
 * post-execution reconciliation (§17), and evidence requirements.
 */

import {
  ApprovalRecord,
  AuditRecord,
  AuditSnapshotPoint,
  DataSource,
  Proposal,
  ReconciliationResult,
  SimulationResult,
  ValidationResult,
} from './types';

// ─── Audit Store (§14.3 append-only) ──────────────────────────────

export class AuditStore {
  private records: AuditRecord[] = [];
  private recordIndex = new Map<string, AuditRecord[]>(); // proposalId -> records

  /** Append a new audit record — never overwrites (§14.3) */
  append(record: AuditRecord): void {
    this.records.push(record);

    const existing = this.recordIndex.get(record.proposalId) ?? [];
    existing.push(record);
    this.recordIndex.set(record.proposalId, existing);
  }

  /** Get all audit records for a proposal */
  getByProposal(proposalId: string): AuditRecord[] {
    return this.recordIndex.get(proposalId) ?? [];
  }

  /** Check if an audit record exists for a proposal at a given snapshot point */
  hasSnapshot(proposalId: string, point: AuditSnapshotPoint): boolean {
    const records = this.recordIndex.get(proposalId) ?? [];
    return records.some(r => r.snapshotPoint === point);
  }

  /** Get total record count */
  count(): number {
    return this.records.length;
  }

  /** Get all records (read-only) */
  getAll(): readonly AuditRecord[] {
    return this.records;
  }

  // ─── Snapshot Creators (§14.2) ──────────────────────────────────

  /** Create snapshot before proposal generation */
  snapshotBeforeProposal(
    proposalId: string,
    sources: DataSource[],
  ): AuditRecord {
    const record: AuditRecord = {
      recordId: generateRecordId(),
      proposalId,
      snapshotPoint: AuditSnapshotPoint.BeforeProposalGeneration,
      timestamp: Date.now(),
      sourceSnapshot: sources,
    };
    this.append(record);
    return record;
  }

  /** Create snapshot after validation */
  snapshotAfterValidation(
    proposalId: string,
    proposal: Proposal,
    validationResult: ValidationResult,
  ): AuditRecord {
    const record: AuditRecord = {
      recordId: generateRecordId(),
      proposalId,
      snapshotPoint: AuditSnapshotPoint.AfterValidation,
      timestamp: Date.now(),
      proposalSnapshot: { ...proposal },
      validationResult,
    };
    this.append(record);
    return record;
  }

  /** Create snapshot before approval */
  snapshotBeforeApproval(
    proposalId: string,
    proposal: Proposal,
  ): AuditRecord {
    const record: AuditRecord = {
      recordId: generateRecordId(),
      proposalId,
      snapshotPoint: AuditSnapshotPoint.BeforeApproval,
      timestamp: Date.now(),
      proposalSnapshot: { ...proposal },
      approvalRecords: [...proposal.approvals],
    };
    this.append(record);
    return record;
  }

  /** Create snapshot before signer submission */
  snapshotBeforeSigner(
    proposalId: string,
    proposal: Proposal,
    signerPolicyResult: { passed: boolean; reason?: string },
    payloadHash: string,
  ): AuditRecord {
    const record: AuditRecord = {
      recordId: generateRecordId(),
      proposalId,
      snapshotPoint: AuditSnapshotPoint.BeforeSignerSubmission,
      timestamp: Date.now(),
      proposalSnapshot: { ...proposal },
      signerPolicyResult,
      payloadHash,
    };
    this.append(record);
    return record;
  }

  /** Create snapshot after receipt ingest */
  snapshotAfterReceipt(
    proposalId: string,
    receipt: { success: boolean; txHash?: string; error?: string },
  ): AuditRecord {
    const record: AuditRecord = {
      recordId: generateRecordId(),
      proposalId,
      snapshotPoint: AuditSnapshotPoint.AfterReceiptIngest,
      timestamp: Date.now(),
      receiptOrFailure: receipt,
    };
    this.append(record);
    return record;
  }

  /** Create snapshot after reconciliation */
  snapshotAfterReconciliation(
    proposalId: string,
    reconciliation: { matched: boolean; discrepancies?: string[] },
  ): AuditRecord {
    const record: AuditRecord = {
      recordId: generateRecordId(),
      proposalId,
      snapshotPoint: AuditSnapshotPoint.AfterReconciliation,
      timestamp: Date.now(),
      reconciliationResult: reconciliation,
    };
    this.append(record);
    return record;
  }

  // ─── Completeness Check (§14.1) ────────────────────────────────

  /** Verify all required audit artifacts exist for an execution-bound action */
  verifyCompleteness(proposalId: string): {
    complete: boolean;
    missing: AuditSnapshotPoint[];
  } {
    const required: AuditSnapshotPoint[] = [
      AuditSnapshotPoint.BeforeProposalGeneration,
      AuditSnapshotPoint.AfterValidation,
      AuditSnapshotPoint.BeforeApproval,
      AuditSnapshotPoint.BeforeSignerSubmission,
    ];

    const missing = required.filter(point => !this.hasSnapshot(proposalId, point));
    return { complete: missing.length === 0, missing };
  }

  /** Verify post-execution audit completeness */
  verifyPostExecutionCompleteness(proposalId: string): {
    complete: boolean;
    missing: AuditSnapshotPoint[];
  } {
    const required: AuditSnapshotPoint[] = [
      AuditSnapshotPoint.AfterReceiptIngest,
      AuditSnapshotPoint.AfterReconciliation,
    ];

    const missing = required.filter(point => !this.hasSnapshot(proposalId, point));
    return { complete: missing.length === 0, missing };
  }
}

// ─── Post-Execution Reconciliation (§17) ──────────────────────────

export function reconcile(
  proposalId: string,
  expected: Record<string, unknown>,
  actual: Record<string, unknown>,
): ReconciliationResult {
  const discrepancies: string[] = [];

  for (const key of Object.keys(expected)) {
    const exp = JSON.stringify(expected[key]);
    const act = JSON.stringify(actual[key]);
    if (exp !== act) {
      discrepancies.push(`${key}: expected ${exp}, got ${act}`);
    }
  }

  return {
    proposalId,
    matched: discrepancies.length === 0,
    expectedState: expected,
    actualState: actual,
    discrepancies,
    timestamp: Date.now(),
  };
}

// ─── Helpers ──────────────────────────────────────────────────────

function generateRecordId(): string {
  return `AUD-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}
