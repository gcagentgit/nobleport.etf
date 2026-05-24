/**
 * NoblePort Matter OS — Unified Dashboard Typology
 *
 * Normalizes all system surfaces into 8 operational layers:
 *   1. Revenue
 *   2. Operations
 *   3. Compliance
 *   4. Governance
 *   5. AI Orchestration
 *   6. Infrastructure
 *   7. Audit / Truth Layer
 *   8. Client Experience
 *
 * Every module, widget, and data source maps to exactly one layer.
 * The executive command center renders one panel per layer.
 */

import type { DeploymentBadge, Health } from './types';

// ─── Layer Taxonomy ───────────────────────────────────────────────────────────

export type OperationalLayer =
  | 'revenue'
  | 'operations'
  | 'compliance'
  | 'governance'
  | 'ai_orchestration'
  | 'infrastructure'
  | 'audit'
  | 'client_experience';

export interface LayerDefinition {
  id: OperationalLayer;
  name: string;
  subtitle: string;
  systems: string[];
  health: Health;
}

export const LAYER_DEFINITIONS: LayerDefinition[] = [
  {
    id: 'revenue',
    name: 'Revenue',
    subtitle: 'Lead → Cash Engine',
    systems: ['Stephanie.ai Intake', 'GCagent.ai', 'Stripe', 'HubSpot', 'QuickBooks'],
    health: 'healthy',
  },
  {
    id: 'operations',
    name: 'Operations',
    subtitle: 'Field Execution OS',
    systems: ['GCagent.ai', 'PermitStream.ai', 'Buildertrend', 'Scheduling Engine'],
    health: 'healthy',
  },
  {
    id: 'compliance',
    name: 'Compliance',
    subtitle: 'Human-Gated Institutional Controls',
    systems: ['Cyborg.ai', 'KYC Engine', 'Permit Compliance', 'Risk Flags'],
    health: 'healthy',
  },
  {
    id: 'governance',
    name: 'Governance',
    subtitle: 'DAO & Treasury Approval',
    systems: ['Nemoclaw', 'Multi-sig Gateway', 'Snapshot'],
    health: 'healthy',
  },
  {
    id: 'ai_orchestration',
    name: 'AI Orchestration',
    subtitle: 'Stephanie.ai Agent Mesh',
    systems: ['Stephanie.ai', 'GCagent.ai', 'PermitStream.ai', 'Cyborg.ai', 'DeepAgent'],
    health: 'degraded',
  },
  {
    id: 'infrastructure',
    name: 'Infrastructure',
    subtitle: 'Sovereign Infrastructure Mesh',
    systems: ['FastAPI', 'Redis', 'PostgreSQL', 'LiveKit', 'ElevenLabs'],
    health: 'healthy',
  },
  {
    id: 'audit',
    name: 'Audit & Truth',
    subtitle: 'Immutable Operational Ledger',
    systems: ['AuditBeacon', 'Merkle Anchors', 'EIP-712 Registry'],
    health: 'healthy',
  },
  {
    id: 'client_experience',
    name: 'Client Experience',
    subtitle: 'Stephanie.ai Front Door',
    systems: ['Voice Agent', 'Avatar', 'Homeowner Portal', 'Intake Queue'],
    health: 'healthy',
  },
];

// ─── Module Registry ──────────────────────────────────────────────────────────

export type ModuleStatus = 'LIVE' | 'STAGED' | 'MODELED' | 'EXTERNAL' | 'SPECIFICATION' | 'BLOCKED' | 'ARCHIVED';

export interface SystemModule {
  id: string;
  name: string;
  layer: OperationalLayer;
  status: ModuleStatus;
  health: Health;
  description: string;
  dependencies: string[];
}

export const SYSTEM_MODULES: SystemModule[] = [
  // ── Revenue Layer ──
  {
    id: 'stephanie-intake',
    name: 'Stephanie.ai Intake',
    layer: 'revenue',
    status: 'LIVE',
    health: 'healthy',
    description: 'Voice-enabled lead capture and project intake',
    dependencies: ['livekit', 'elevenlabs'],
  },
  {
    id: 'proposal-engine',
    name: 'Proposal Generation',
    layer: 'revenue',
    status: 'LIVE',
    health: 'healthy',
    description: 'Estimate creation, pricing, and proposal delivery',
    dependencies: ['fastapi', 'postgres'],
  },
  {
    id: 'deposit-collection',
    name: 'Deposit Collection',
    layer: 'revenue',
    status: 'STAGED',
    health: 'healthy',
    description: 'Stripe-powered deposit invoicing and payment tracking',
    dependencies: ['stripe'],
  },
  {
    id: 'awo-tracking',
    name: 'AWO Tracking',
    layer: 'revenue',
    status: 'LIVE',
    health: 'healthy',
    description: 'Change order detection, pricing, and margin recovery',
    dependencies: ['fastapi', 'postgres'],
  },
  {
    id: 'invoice-ar',
    name: 'Invoice & AR',
    layer: 'revenue',
    status: 'STAGED',
    health: 'healthy',
    description: 'Milestone invoicing and accounts receivable aging',
    dependencies: ['stripe', 'quickbooks'],
  },
  {
    id: 'crm-sync',
    name: 'CRM Sync',
    layer: 'revenue',
    status: 'STAGED',
    health: 'healthy',
    description: 'Bidirectional HubSpot pipeline synchronization',
    dependencies: ['hubspot'],
  },

  // ── Operations Layer ──
  {
    id: 'gcagent-ops',
    name: 'GCagent.ai',
    layer: 'operations',
    status: 'LIVE',
    health: 'healthy',
    description: 'Crew orchestration, scheduling, and project coordination',
    dependencies: ['langgraph', 'redis'],
  },
  {
    id: 'permitstream',
    name: 'PermitStream.ai',
    layer: 'operations',
    status: 'STAGED',
    health: 'degraded',
    description: 'Permit intelligence and AHJ workflow tracking (MA)',
    dependencies: ['playwright', 'postgres'],
  },
  {
    id: 'scheduling',
    name: 'Scheduling Engine',
    layer: 'operations',
    status: 'LIVE',
    health: 'healthy',
    description: 'Job timeline management and crew calendar',
    dependencies: ['google_calendar'],
  },
  {
    id: 'inspection-tracking',
    name: 'Inspection Tracking',
    layer: 'operations',
    status: 'MODELED',
    health: 'healthy',
    description: 'Municipal inspection scheduling and pass/fail tracking',
    dependencies: [],
  },
  {
    id: 'punch-list',
    name: 'Punch List System',
    layer: 'operations',
    status: 'MODELED',
    health: 'healthy',
    description: 'Closeout punch list management and photo documentation',
    dependencies: [],
  },

  // ── Compliance Layer ──
  {
    id: 'permit-compliance',
    name: 'Permit Compliance',
    layer: 'compliance',
    status: 'STAGED',
    health: 'healthy',
    description: 'Jurisdiction-level permit requirement checking',
    dependencies: ['permitstream'],
  },
  {
    id: 'kyc-queue',
    name: 'KYC Queue',
    layer: 'compliance',
    status: 'MODELED',
    health: 'healthy',
    description: 'Identity verification for investors and partners',
    dependencies: [],
  },
  {
    id: 'risk-flags',
    name: 'Risk Flags',
    layer: 'compliance',
    status: 'MODELED',
    health: 'healthy',
    description: 'Automated compliance warning generation',
    dependencies: ['cyborg-ai'],
  },
  {
    id: 'command-freeze',
    name: 'Command Freeze',
    layer: 'compliance',
    status: 'LIVE',
    health: 'healthy',
    description: 'Production command lockdown for autonomous operations',
    dependencies: [],
  },

  // ── Governance Layer ──
  {
    id: 'nemoclaw',
    name: 'Nemoclaw Policy Engine',
    layer: 'governance',
    status: 'MODELED',
    health: 'healthy',
    description: 'Proposal lifecycle, multi-sig approval, separation of duties',
    dependencies: ['ethers'],
  },
  {
    id: 'treasury-approval',
    name: 'Treasury Approval Queue',
    layer: 'governance',
    status: 'MODELED',
    health: 'healthy',
    description: 'Human-gated financial disbursement approval',
    dependencies: ['nemoclaw'],
  },
  {
    id: 'dao-votes',
    name: 'DAO Voting',
    layer: 'governance',
    status: 'MODELED',
    health: 'healthy',
    description: 'Governance token voting and snapshot integration',
    dependencies: [],
  },

  // ── AI Orchestration Layer ──
  {
    id: 'stephanie-orchestrator',
    name: 'Stephanie.ai',
    layer: 'ai_orchestration',
    status: 'LIVE',
    health: 'healthy',
    description: 'Executive voice orchestration and task routing',
    dependencies: ['livekit', 'elevenlabs', 'langgraph'],
  },
  {
    id: 'gcagent-agent',
    name: 'GCagent.ai Agent',
    layer: 'ai_orchestration',
    status: 'LIVE',
    health: 'healthy',
    description: 'Construction operations supervisor agent',
    dependencies: ['langgraph', 'redis'],
  },
  {
    id: 'permitstream-agent',
    name: 'PermitStream.ai Agent',
    layer: 'ai_orchestration',
    status: 'STAGED',
    health: 'degraded',
    description: 'Permit forecasting and AHJ workflow agent',
    dependencies: ['playwright'],
  },
  {
    id: 'cyborg-agent',
    name: 'Cyborg.ai',
    layer: 'ai_orchestration',
    status: 'MODELED',
    health: 'healthy',
    description: 'Compliance and governance enforcement agent',
    dependencies: [],
  },
  {
    id: 'deepagent',
    name: 'DeepAgent',
    layer: 'ai_orchestration',
    status: 'MODELED',
    health: 'healthy',
    description: 'Long-horizon research and diligence agent',
    dependencies: [],
  },

  // ── Infrastructure Layer ──
  {
    id: 'fastapi-gateway',
    name: 'FastAPI Gateway',
    layer: 'infrastructure',
    status: 'LIVE',
    health: 'healthy',
    description: 'Primary REST API gateway',
    dependencies: ['postgres', 'redis'],
  },
  {
    id: 'voice-pipeline',
    name: 'Voice Pipeline',
    layer: 'infrastructure',
    status: 'LIVE',
    health: 'healthy',
    description: 'LiveKit + ElevenLabs STT/TTS pipeline',
    dependencies: ['livekit', 'elevenlabs'],
  },
  {
    id: 'database',
    name: 'PostgreSQL',
    layer: 'infrastructure',
    status: 'LIVE',
    health: 'healthy',
    description: 'Primary data store',
    dependencies: [],
  },
  {
    id: 'task-queue',
    name: 'Redis Task Queue',
    layer: 'infrastructure',
    status: 'STAGED',
    health: 'healthy',
    description: 'Async task queue for agent orchestration',
    dependencies: ['redis'],
  },

  // ���─ Audit & Truth Layer ──
  // NOTE: "Proposed Audit Architecture" (SPECIFICATION) is separated from
  // "Production Logging" (LIVE). Do not conflate these in any materials.
  {
    id: 'production-logging',
    name: 'Production Logging',
    layer: 'audit',
    status: 'LIVE',
    health: 'healthy',
    description: 'Structured application logs (stdout, Sentry, file)',
    dependencies: ['python-logging', 'sentry'],
  },
  {
    id: 'awo-history',
    name: 'AWO History',
    layer: 'audit',
    status: 'LIVE',
    health: 'healthy',
    description: 'Change order evidence chain in PostgreSQL',
    dependencies: ['postgres'],
  },
  {
    id: 'permit-history',
    name: 'Permit History',
    layer: 'audit',
    status: 'STAGED',
    health: 'healthy',
    description: 'Permit application and decision log',
    dependencies: ['postgres'],
  },
  {
    id: 'audit-beacon',
    name: 'AuditBeacon (Proposed)',
    layer: 'audit',
    status: 'SPECIFICATION',
    health: 'unknown',
    description: 'PROPOSED: Pre-write event logging with merkle anchoring',
    dependencies: [],
  },
  {
    id: 'merkle-anchors',
    name: 'Merkle Anchors (Proposed)',
    layer: 'audit',
    status: 'SPECIFICATION',
    health: 'unknown',
    description: 'PROPOSED: Daily merkle root proof publication to L2',
    dependencies: ['arbitrum'],
  },

  // ── Client Experience Layer ──
  {
    id: 'voice-intake',
    name: 'Voice Intake (Inbound)',
    layer: 'client_experience',
    status: 'STAGED',
    health: 'healthy',
    description: 'Homeowner voice consultation via Stephanie.ai',
    dependencies: ['livekit', 'elevenlabs'],
  },
  {
    id: 'voice-outbound',
    name: 'Voice Intake (Outbound)',
    layer: 'client_experience',
    status: 'STAGED',
    health: 'healthy',
    description: 'Proactive outbound calls for follow-ups',
    dependencies: ['livekit', 'elevenlabs', '3cx'],
  },
  {
    id: 'streaming-ui',
    name: 'Streaming Transcript UI',
    layer: 'client_experience',
    status: 'STAGED',
    health: 'healthy',
    description: 'Real-time voice transcript in dashboard console',
    dependencies: ['livekit', 'nextjs'],
  },
  {
    id: 'avatar-render',
    name: 'Real-Time Avatar',
    layer: 'client_experience',
    status: 'SPECIFICATION',
    health: 'unknown',
    description: 'SPEC: Visual avatar for video (latency requirements not met)',
    dependencies: ['webrtc', 'gpu'],
  },
  {
    id: 'homeowner-portal',
    name: 'Homeowner Portal',
    layer: 'client_experience',
    status: 'SPECIFICATION',
    health: 'unknown',
    description: 'SPEC: Client-facing project status dashboard',
    dependencies: ['nextjs'],
  },
  {
    id: 'multilingual-voice',
    name: 'Multilingual Voice',
    layer: 'client_experience',
    status: 'MODELED',
    health: 'unknown',
    description: 'Multi-language intake (Spanish, Portuguese)',
    dependencies: ['elevenlabs-multilingual'],
  },
  {
    id: 'sentiment-analytics',
    name: 'Customer Sentiment',
    layer: 'client_experience',
    status: 'MODELED',
    health: 'unknown',
    description: 'Emotion scoring and satisfaction tracking',
    dependencies: [],
  },
];

// ─── Dashboard Widget Definitions ─────────────────────────────────────────────

export interface DashboardWidget {
  id: string;
  label: string;
  layer: OperationalLayer;
  source: string;
  deploymentStatus: ModuleStatus;
}

export const EXECUTIVE_WIDGETS: DashboardWidget[] = [
  // Revenue
  { id: 'w-leads', label: 'Open Leads', layer: 'revenue', source: 'Intake system', deploymentStatus: 'LIVE' },
  { id: 'w-estimates', label: 'Estimates Pending', layer: 'revenue', source: 'Proposal queue', deploymentStatus: 'LIVE' },
  { id: 'w-deposits', label: 'Deposit Collection', layer: 'revenue', source: 'Stripe', deploymentStatus: 'STAGED' },
  { id: 'w-active-jobs', label: 'Active Jobs', layer: 'revenue', source: 'GCagent', deploymentStatus: 'LIVE' },
  { id: 'w-awos', label: 'AWOs', layer: 'revenue', source: 'AWO ledger', deploymentStatus: 'LIVE' },
  { id: 'w-ar-aging', label: 'Invoice Aging', layer: 'revenue', source: 'AR dashboard', deploymentStatus: 'STAGED' },
  { id: 'w-margin', label: 'Margin Tracker', layer: 'revenue', source: 'CFO system', deploymentStatus: 'MODELED' },

  // Operations
  { id: 'w-permit-queue', label: 'Permit Queue', layer: 'operations', source: 'PermitStream', deploymentStatus: 'STAGED' },
  { id: 'w-inspections', label: 'Inspection Countdowns', layer: 'operations', source: 'AHJ tracker', deploymentStatus: 'MODELED' },
  { id: 'w-crew-util', label: 'Crew Utilization', layer: 'operations', source: 'Scheduling', deploymentStatus: 'MODELED' },
  { id: 'w-punch-pct', label: 'Punch List %', layer: 'operations', source: 'Closeout', deploymentStatus: 'MODELED' },

  // Client Experience
  { id: 'w-live-calls', label: 'Live Intake Calls', layer: 'client_experience', source: 'LiveKit', deploymentStatus: 'LIVE' },
  { id: 'w-voice-status', label: 'Voice Agent Status', layer: 'client_experience', source: 'ElevenLabs', deploymentStatus: 'LIVE' },
  { id: 'w-avatar-latency', label: 'Avatar Latency', layer: 'client_experience', source: 'WebRTC', deploymentStatus: 'MODELED' },
  { id: 'w-intake-queue', label: 'Homeowner Intake Queue', layer: 'client_experience', source: 'Stephanie.ai', deploymentStatus: 'LIVE' },
  { id: 'w-sentiment', label: 'Customer Sentiment', layer: 'client_experience', source: 'Analytics', deploymentStatus: 'MODELED' },

  // Compliance
  { id: 'w-kyc', label: 'KYC Queue', layer: 'compliance', source: 'Identity', deploymentStatus: 'MODELED' },
  { id: 'w-permit-comply', label: 'Permit Compliance', layer: 'compliance', source: 'PermitStream', deploymentStatus: 'STAGED' },
  { id: 'w-risk', label: 'Risk Flags', layer: 'compliance', source: 'Cyborg.ai', deploymentStatus: 'MODELED' },
  { id: 'w-audit-exceptions', label: 'Audit Exceptions', layer: 'compliance', source: 'Manual review', deploymentStatus: 'MODELED' },

  // Governance
  { id: 'w-dao-votes', label: 'DAO Votes', layer: 'governance', source: 'Snapshot', deploymentStatus: 'MODELED' },
  { id: 'w-treasury-queue', label: 'Treasury Approval Queue', layer: 'governance', source: 'Multi-sig', deploymentStatus: 'MODELED' },

  // AI Orchestration
  { id: 'w-agent-health', label: 'Agent Health', layer: 'ai_orchestration', source: 'Orchestrator', deploymentStatus: 'MODELED' },
  { id: 'w-queue-depth', label: 'Queue Depth', layer: 'ai_orchestration', source: 'Redis', deploymentStatus: 'STAGED' },
  { id: 'w-latency', label: 'Latency Metrics', layer: 'ai_orchestration', source: 'APM', deploymentStatus: 'MODELED' },
  { id: 'w-decision-trace', label: 'Decision Trace', layer: 'ai_orchestration', source: 'LangSmith', deploymentStatus: 'MODELED' },

  // Infrastructure
  { id: 'w-api-health', label: 'API Gateway', layer: 'infrastructure', source: 'FastAPI', deploymentStatus: 'LIVE' },
  { id: 'w-voice-pipe', label: 'Voice Pipeline', layer: 'infrastructure', source: 'LiveKit', deploymentStatus: 'LIVE' },
  { id: 'w-db-health', label: 'Database', layer: 'infrastructure', source: 'PostgreSQL', deploymentStatus: 'LIVE' },

  // Audit
  { id: 'w-audit-events', label: 'AuditBeacon Events', layer: 'audit', source: 'Logger', deploymentStatus: 'MODELED' },
  { id: 'w-merkle', label: 'Merkle Anchors', layer: 'audit', source: 'Arbitrum', deploymentStatus: 'MODELED' },
  { id: 'w-permit-hist', label: 'Permit History', layer: 'audit', source: 'PermitStream', deploymentStatus: 'STAGED' },
  { id: 'w-sig-registry', label: 'Signature Registry', layer: 'audit', source: 'EIP-712', deploymentStatus: 'MODELED' },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

export function getModulesByLayer(layer: OperationalLayer): SystemModule[] {
  return SYSTEM_MODULES.filter((m) => m.layer === layer);
}

export function getWidgetsByLayer(layer: OperationalLayer): DashboardWidget[] {
  return EXECUTIVE_WIDGETS.filter((w) => w.layer === layer);
}

export function getLiveModules(): SystemModule[] {
  return SYSTEM_MODULES.filter((m) => m.status === 'LIVE');
}

export function getLayerHealth(layer: OperationalLayer): Health {
  const modules = getModulesByLayer(layer);
  if (modules.some((m) => m.health === 'unhealthy')) return 'unhealthy';
  if (modules.some((m) => m.health === 'degraded')) return 'degraded';
  if (modules.every((m) => m.health === 'healthy')) return 'healthy';
  return 'unknown';
}

export function getStatusCounts(): Record<ModuleStatus, number> {
  const counts: Record<ModuleStatus, number> = {
    LIVE: 0, STAGED: 0, MODELED: 0, EXTERNAL: 0, SPECIFICATION: 0, BLOCKED: 0, ARCHIVED: 0,
  };
  for (const m of SYSTEM_MODULES) {
    counts[m.status]++;
  }
  return counts;
}
