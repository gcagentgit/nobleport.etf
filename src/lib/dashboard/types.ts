/**
 * NoblePort Mission Control — shared dashboard contracts.
 *
 * These types describe the operator-grade execution console feed.
 * Every panel reads against these contracts; the backend (FastAPI gateway,
 * LangGraph supervisor) and the mock fixtures both implement the same shapes.
 */

export type Health = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
export type Severity = 'info' | 'warn' | 'critical';
export type Trend = 'up' | 'down' | 'flat';

export interface KpiTile {
  id: string;
  label: string;
  value: string;
  raw: number;
  unit?: string;
  delta?: number;
  deltaLabel?: string;
  trend?: Trend;
  source: string;
  href?: string;
  health?: Health;
  hint?: string;
}

export interface PipelineStage {
  id: string;
  name: string;
  count: number;
  value: number;
  staleCount: number;
}

export interface Deal {
  id: string;
  name: string;
  client: string;
  stage: string;
  value: number;
  ageDays: number;
  owner: string;
  nextAction: string;
  blockers: string[];
  depositRequired: boolean;
  depositCollected: boolean;
}

export interface Invoice {
  id: string;
  number: string;
  job: string;
  client: string;
  amount: number;
  daysOverdue: number;
  status: 'sent' | 'partial' | 'overdue' | 'collected' | 'draft';
}

export interface CashPosition {
  asOf: string;
  operating: number;
  reserve: number;
  escrow: number;
  pendingDeposits: number;
  pendingPayables: number;
  runwayDays: number;
}

export interface Job {
  id: string;
  code: string;
  name: string;
  client: string;
  pm: string;
  phase: 'pre-con' | 'permitting' | 'mobilization' | 'production' | 'punch' | 'closeout';
  contractValue: number;
  billedToDate: number;
  costToDate: number;
  gpForecast: number;
  gpFloor: number;
  scheduleVariance: number;
  health: Health;
  blockers: string[];
  depositCollected: boolean;
  nextMilestone: string;
  nextMilestoneAt: string;
}

export interface Permit {
  id: string;
  number: string;
  job: string;
  ahj: string;
  type: string;
  status: 'intake' | 'review' | 'corrections' | 'issued' | 'denied' | 'expired';
  submittedAt: string;
  ageDays: number;
  forecastIssueAt: string;
  reviewer?: string;
  zoningFlags: string[];
}

export interface PermitForecastBucket {
  ahj: string;
  medianDays: number;
  p90Days: number;
  open: number;
  issuedThisMonth: number;
}

export interface Agent {
  id: string;
  name: string;
  family: 'Stephanie' | 'GCagent' | 'PermitStream' | 'Cyborg' | 'DeepAgent' | 'KUZO' | 'Other';
  role: string;
  health: Health;
  queueDepth: number;
  inFlight: number;
  p95LatencyMs: number;
  errorRate: number;
  uptime30d: number;
  lastHeartbeat: string;
  killSwitchArmed: boolean;
  currentTask?: string;
}

export interface AgentMeshSummary {
  total: number;
  healthy: number;
  degraded: number;
  unhealthy: number;
  totalQueue: number;
  totalInFlight: number;
  topLatencyMs: number;
}

export interface ComplianceAlert {
  id: string;
  ts: string;
  severity: Severity;
  category: 'sanctions' | 'erc1400' | 'policy' | 'signature' | 'kill-switch' | 'kyc';
  subject: string;
  detail: string;
  agent?: string;
  resolved: boolean;
}

export interface KillSwitch {
  id: string;
  scope: string;
  armed: boolean;
  lastTriggeredAt?: string;
  controller: string;
  description: string;
}

export interface AuditEntry {
  id: string;
  ts: string;
  operator: string;
  agent?: string;
  action: string;
  subject: string;
  approval: 'auto' | 'human' | 'dao' | 'multi-sig' | 'none';
  hash: string;
  prevHash: string;
  anchor?: string;
  status: 'committed' | 'pending' | 'rejected';
}

export interface VoiceSessionSummary {
  active: boolean;
  sessionId?: string;
  participants: number;
  latencyMs: number;
  packetLossPct: number;
  asrModel: string;
  ttsVoice: string;
  startedAt?: string;
  routedTo: string[];
}

export interface VoiceTranscriptTurn {
  id: string;
  ts: string;
  speaker: 'operator' | 'stephanie' | 'caller';
  text: string;
  routed?: string;
}

export interface RevenueRule {
  id: string;
  rule: string;
  status: 'enforced' | 'warning' | 'override';
  violations: number;
}

export interface DashboardOverview {
  generatedAt: string;
  kpis: KpiTile[];
  alerts: ComplianceAlert[];
  agentSummary: AgentMeshSummary;
  cash: CashPosition;
  pipeline: PipelineStage[];
  upcomingMilestones: { jobCode: string; milestone: string; at: string }[];
}

// ── Matter OS: RAOS Memory ──────────────────────────────────────────

export type MemoryScope = 'global' | 'stephanie' | 'gcagent' | 'permitstream' | 'cyborg' | 'audit_beacon';

export interface OperationalMemoryEntry {
  key: string;
  value: unknown;
  category: string;
  entityType?: string;
  entityId?: string;
  writtenBy?: string;
  version: number;
  updatedAt: string;
}

// ── Matter OS: PermitStream ─────────────────────────────────────────

export interface PermitDetail extends Permit {
  internalRef: string;
  deficiencyScore: number;
  zoningRiskScore: number;
  completenessScore: number;
  correctionRounds: number;
  checklist: PermitChecklistItem[];
}

export interface PermitChecklistItem {
  item: string;
  required: boolean;
  complete: boolean;
  category: string;
}

// ── Matter OS: AWO Ledger ───────────────────────────────────────────

export interface ChangeOrder {
  id: string;
  jobId: string;
  changeOrderNumber: string;
  title: string;
  reason: string;
  status: 'draft' | 'proposed' | 'sent' | 'approved' | 'in_progress' | 'completed' | 'rejected' | 'voided';
  laborCost: number;
  materialCost: number;
  markupPercent: number;
  totalAmount: number;
  scheduleImpactDays: number;
  approvedBy?: string;
  aiSuggested: boolean;
}

// ── Matter OS: Intake ───────────────────────────────────────────────

export interface IntakeLead {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  source: string;
  status: string;
  propertyAddress?: string;
  city?: string;
  estimatedValue?: number;
  assignedTo?: string;
  homeownerScore?: number;
  createdAt: string;
}

// ── Matter OS: Notifications ────────────────────────────────────────

export interface SystemNotification {
  id: string;
  channel: string;
  priority: 'low' | 'normal' | 'high' | 'critical';
  category: string;
  recipient: string;
  title: string;
  body?: string;
  read: boolean;
  actionUrl?: string;
  createdAt: string;
}
