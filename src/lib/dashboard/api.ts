/**
 * Dashboard API client.
 *
 * Always calls the FastAPI gateway at `DASHBOARD_API_BASE`. There is no
 * runtime fallback to local fixtures — operators see honest backend state.
 * If the gateway is unreachable or returns a non-2xx, the request throws
 * and the route surfaces the error through Next.js' error boundary.
 *
 * Configuration:
 *   DASHBOARD_API_BASE   server-side env var (default: http://localhost:8000/api/v1/dashboard)
 *   DASHBOARD_API_TOKEN  optional bearer token, forwarded as Authorization
 */

import 'server-only';
import type {
  Agent,
  AgentMeshSummary,
  AuditEntry,
  CashPosition,
  ComplianceAlert,
  DashboardOverview,
  Deal,
  Invoice,
  Job,
  KillSwitch,
  Permit,
  PermitForecastBucket,
  PipelineStage,
  RevenueRule,
  VoiceSessionSummary,
  VoiceTranscriptTurn,
} from './types';

const DEFAULT_BASE = 'http://localhost:8000/api/v1/dashboard';

export type DataSource = 'live' | 'fixture' | 'mixed' | 'unknown';

export interface ApiResult<T> {
  data: T;
  source: DataSource;
}

export class DashboardApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly url: string,
    readonly bodySnippet?: string,
  ) {
    super(message);
    this.name = 'DashboardApiError';
  }
}

function apiBase(): string {
  return process.env.DASHBOARD_API_BASE ?? DEFAULT_BASE;
}

function authHeader(): Record<string, string> {
  const token = process.env.DASHBOARD_API_TOKEN;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function get<T>(path: string): Promise<ApiResult<T>> {
  const url = `${apiBase()}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: 'GET',
      headers: { Accept: 'application/json', ...authHeader() },
      cache: 'no-store',
      // Operator console: don't tolerate slow upstreams silently.
      signal: AbortSignal.timeout(5_000),
    });
  } catch (err) {
    const reason = err instanceof Error ? err.message : 'unknown error';
    throw new DashboardApiError(
      `gateway unreachable: ${reason}`,
      0,
      url,
    );
  }

  if (!res.ok) {
    let snippet: string | undefined;
    try {
      snippet = (await res.text()).slice(0, 500);
    } catch {
      /* ignore */
    }
    throw new DashboardApiError(
      `gateway returned ${res.status} ${res.statusText}`,
      res.status,
      url,
      snippet,
    );
  }

  const source = (res.headers.get('x-data-source') ?? 'unknown') as DataSource;
  const data = (await res.json()) as T;
  return { data, source };
}

// ---------------------------------------------------------------------------
// Endpoint wrappers
// ---------------------------------------------------------------------------

export const fetchOverview = () => get<DashboardOverview>('/overview');

export const fetchRevenue = () =>
  get<{
    pipeline: PipelineStage[];
    deals: Deal[];
    invoices: Invoice[];
    cash: CashPosition;
    rules: RevenueRule[];
  }>('/revenue');

export const fetchJobs = () => get<{ jobs: Job[] }>('/jobs');

export const fetchPermits = () =>
  get<{ permits: Permit[]; forecast: PermitForecastBucket[] }>('/permits');

export const fetchAgents = () =>
  get<{ agents: Agent[]; summary: AgentMeshSummary }>('/agents');

export const fetchCompliance = () =>
  get<{ alerts: ComplianceAlert[]; killSwitches: KillSwitch[] }>('/compliance');

export const fetchAudit = (limit = 50) =>
  get<{ entries: AuditEntry[]; limit: number }>(`/audit?limit=${limit}`);

export const fetchVoice = () =>
  get<{ session: VoiceSessionSummary; transcript: VoiceTranscriptTurn[] }>('/voice');

export const fetchHealth = () =>
  get<{ status: string; service: string; ts: string }>('/health');
