/**
 * NoblePort OS — Core Module
 *
 * Central export for the NoblePort operating system type layer.
 * Provides type-safe contracts for the revenue loop, proof of trust,
 * integration health, ops brief, and top-level OS state.
 */

// ─── Enums ────────────────────────────────────────────────────────────
export { RevenueLoopStage } from './types';

// ─── App Registry ─────────────────────────────────────────────────────
export { APP_REGISTRY, OS_PRINCIPLES, appsByOffice, appStatusSummary } from './apps';
export type { NoblePortApp, AppOffice, AppStatus } from './apps';

// ─── Type-only re-exports ─────────────────────────────────────────────
export type {
  // Revenue Loop
  RevenueLoopPosition,
  RevenueLoopStageHealth,
  RevenueLoopHealth,
  RevenueLoopState,

  // Proof of Trust
  ProofOfTrust,
  TrustScoreDimensions,
  TrustScore,
  ProofOfTrustState,

  // Integrations
  IntegrationConnectionStatus,
  IntegrationStatus,
  IntegrationHealth,

  // Ops Brief
  OpsBriefItem,
  OpsBrief,

  // Agent Mesh
  AgentMeshState,

  // Top-level state
  NoblePortOSState,
} from './types';
