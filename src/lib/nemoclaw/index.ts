/**
 * Nemoclaw v1 — Execution Policy Module
 *
 * Central export for the Nemoclaw execution policy framework.
 * Provides type-safe enforcement of operating modes, action classes,
 * approval thresholds, signer gateway policy, proposal lifecycle,
 * circuit breakers, audit trails, and event processing.
 *
 * @see §1-22 of the Nemoclaw v1 Execution Policy Specification
 */

// ─── Types ─────────────────────────────────────────────────────────
export {
  // Operating modes (§3)
  OperatingMode,
  // Action classes (§4)
  ActionClass,
  // Roles (§6)
  Role,
  APPROVAL_ROLES,
  PROPOSAL_CREATOR_ROLES,
  // Approval thresholds (§5)
  ExposureTier,
  ApprovalThreshold,
  APPROVAL_THRESHOLDS,
  RWA_EXECUTION_THRESHOLD,
  // Proposals (§8)
  ProposalState,
  Proposal,
  ApprovalRecord,
  SimulationResult,
  ValidationResult,
  ValidationCheck,
  // Data sources (§7)
  DataSourcePrecedence,
  DataSource,
  // Events (§9)
  NemoclawEvent,
  // Signer gateway (§10)
  SignerPayload,
  SignerGatewayConfig,
  // Position & exposure (§12)
  PositionLimits,
  ExposureConfig,
  // Circuit breakers (§15)
  CircuitBreakerTrigger,
  CircuitBreakerState,
  KillSwitchScope,
  KillSwitchAction,
  // Incidents (§18)
  IncidentSeverity,
  Incident,
  // Audit (§14)
  AuditSnapshotPoint,
  AuditRecord,
  // Freshness (§7.3)
  FreshnessConfig,
  DEFAULT_FRESHNESS_CONFIG,
  // Policy decision (§2.4)
  PolicyDecision,
  // Emergency override (§16)
  EmergencyOverride,
  // Reconciliation (§17)
  ReconciliationResult,
} from './types';

// ─── Policy Engine (§2-6, §11) ────────────────────────────────────
export {
  evaluatePolicy,
  resolveExposureTier,
  resolveApprovalThreshold,
  canCreateProposal,
  canApproveExecution,
  validateRoleForAction,
  checkSeparationOfDuties,
  checkApprovalsComplete,
  checkPreExecutionGuardrails,
  getModePermissions,
  isActionAllowedInMode,
} from './policy';
export type { PreExecutionCheckResult } from './policy';

// ─── Validation Wall (§7) ─────────────────────────────────────────
export {
  validateProposal,
  DuplicateDetector,
  resolveSourceConflicts,
  checkFreshness,
} from './validation';

// ─── Signer Gateway (§10) ─────────────────────────────────────────
export {
  evaluateSignerRequest,
  createSignerGatewayConfig,
  DEFAULT_ALLOWED_CHAINS,
  SignerRejectionReason,
} from './signer-gateway';
export type { SignerGatewayResult } from './signer-gateway';

// ─── Proposal Lifecycle (§8, §13) ─────────────────────────────────
export { ProposalManager } from './proposal';

// ─── Circuit Breakers & Kill Switches (§15-16, §18) ──────────────
export { CircuitBreakerManager } from './circuit-breaker';
export type { CircuitBreakerConfig } from './circuit-breaker';

// ─── Audit Trail (§14, §17) ──────────────────────────────────────
export { AuditStore, reconcile } from './audit';

// ─── Events & Idempotency (§9) ───────────────────────────────────
export {
  EventProcessor,
  IdempotencyEnforcer,
  ReplayProtector,
  createEvent,
} from './events';
