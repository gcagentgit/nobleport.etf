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

// ─── Enums & Runtime Values ──────────────────────────────────────
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
  APPROVAL_THRESHOLDS,
  RWA_EXECUTION_THRESHOLD,
  buildRwaThreshold,
  // Proposals (§8)
  ProposalState,
  // Data sources (§7)
  DataSourcePrecedence,
  // Circuit breakers (§15)
  CircuitBreakerTrigger,
  KillSwitchScope,
  // Incidents (§18)
  IncidentSeverity,
  // Audit (§14)
  AuditSnapshotPoint,
  // Freshness (§7.3)
  DEFAULT_FRESHNESS_CONFIG,
} from './types';

// ─── Type-only exports (required under isolatedModules) ─────────
export type {
  ApprovalThreshold,
  Proposal,
  ApprovalRecord,
  SimulationResult,
  ValidationResult,
  ValidationCheck,
  DataSource,
  NemoclawEvent,
  SignerPayload,
  SignerGatewayConfig,
  PositionLimits,
  ExposureConfig,
  CircuitBreakerState,
  KillSwitchAction,
  Incident,
  AuditRecord,
  FreshnessConfig,
  PolicyDecision,
  EmergencyOverride,
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
  DEFAULT_SANITY_BOUNDS,
} from './validation';
export type { SanityBounds } from './validation';

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
