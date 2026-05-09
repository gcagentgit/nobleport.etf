import { Topbar } from '@/components/dashboard/Topbar';
import { Panel } from '@/components/dashboard/Panel';

export const dynamic = 'force-dynamic';

export default function SettingsPage() {
  return (
    <>
      <Topbar pageTitle="Settings" />
      <main className="flex-1 space-y-4 px-4 py-4 sm:px-6 sm:py-6">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Panel title="Operators" subtitle="role · scope · MFA">
            <ul className="divide-y divide-ink-700 text-sm">
              <Op
                name="m.velasquez"
                role="Operator (Owner)"
                scope="full · multi-sig 1/3"
                mfa
              />
              <Op name="d.iyer" role="PM" scope="jobs · permits" mfa />
              <Op name="a.park" role="PM" scope="jobs · permits" mfa />
              <Op name="ar.collector" role="Service" scope="invoices · outreach" />
              <Op
                name="dao.governor"
                role="DAO (4/7)"
                scope="treasury · gp-floor override"
              />
            </ul>
          </Panel>

          <Panel title="Integrations" subtitle="data sources powering this dashboard">
            <ul className="space-y-2 text-sm">
              <Integration name="ERPNext" status="connected" detail="GL · costing · GP" />
              <Integration name="Stripe" status="connected" detail="deposits · settlements" />
              <Integration name="QuickBooks" status="connected" detail="AR · payables" />
              <Integration name="GCagent" status="connected" detail="construction ops" />
              <Integration name="PermitStream" status="connected" detail="AHJ workflows" />
              <Integration name="Cyborg.ai" status="connected" detail="policy · audit" />
              <Integration name="Stephanie.ai" status="connected" detail="LiveKit + ElevenLabs" />
              <Integration name="Arbitrum anchor" status="connected" detail="audit anchoring" />
              <Integration name="IPFS" status="degraded" detail="document pinning" />
            </ul>
          </Panel>

          <Panel
            title="API Surface"
            subtitle="reads served by FastAPI gateway · /api/v1/dashboard/*"
          >
            <ul className="space-y-1 font-mono text-[12px] text-ink-300">
              <li>GET /api/v1/dashboard/overview <span className="pill-warn">mixed</span></li>
              <li>GET /api/v1/dashboard/revenue <span className="pill-ok">live</span></li>
              <li>GET /api/v1/dashboard/jobs <span className="pill-ok">live</span></li>
              <li>GET /api/v1/dashboard/permits <span className="pill-info">fixture</span></li>
              <li>GET /api/v1/dashboard/agents <span className="pill-info">fixture</span></li>
              <li>GET /api/v1/dashboard/compliance <span className="pill-info">fixture</span></li>
              <li>GET /api/v1/dashboard/audit?limit=N <span className="pill-info">fixture</span></li>
              <li>GET /api/v1/dashboard/voice <span className="pill-info">fixture</span></li>
              <li>GET /api/v1/dashboard/health <span className="pill-ok">live</span></li>
            </ul>
            <p className="mt-3 text-[11px] text-ink-400">
              Configure with <span className="num text-ink-200">DASHBOARD_API_BASE</span> (default
              <span className="num text-ink-200"> http://localhost:8000/api/v1/dashboard</span>)
              and optional <span className="num text-ink-200">DASHBOARD_API_TOKEN</span>. The
              dashboard reads <em>only</em> from this gateway — no client-side fallbacks. Every
              response carries an <span className="num text-ink-200">X-Data-Source</span> header
              ({"live | mixed | fixture"}) which the topbar surfaces to the operator.
            </p>
          </Panel>

          <Panel title="Coverage" subtitle="what's wired live vs awaiting upstream">
            <ul className="space-y-2 text-sm">
              <Coverage label="Revenue · pipeline / cash / AR / rules" status="live" detail="RevenueEngine + Stephanie + invoices/payments tables" />
              <Coverage label="Jobs · production schedule + GP" status="live" detail="jobs table + margin compression detector" />
              <Coverage label="Executive Command KPIs" status="mixed" detail="revenue/jobs live; voice/permits/agents/compliance fixtures" />
              <Coverage label="Permits · AHJ workflows" status="fixture" detail="awaiting PermitStream live API" />
              <Coverage label="AI Agent Mesh" status="fixture" detail="awaiting LangGraph supervisor heartbeat feed" />
              <Coverage label="Compliance · alerts + kill switches" status="fixture" detail="awaiting Cyborg.ai policy log" />
              <Coverage label="Audit chain" status="fixture" detail="awaiting hash-linked audit store + Arbitrum anchor" />
              <Coverage label="Voice console" status="fixture" detail="awaiting LiveKit + Stephanie session telemetry" />
            </ul>
          </Panel>

          <Panel title="Webhooks & Realtime" subtitle="push surfaces to the dashboard">
            <ul className="space-y-2 text-sm text-ink-200">
              <li>• Stripe → /webhooks/stripe (deposits / settlements)</li>
              <li>• QuickBooks → /webhooks/qb (invoice state)</li>
              <li>• GCagent → /webhooks/gc (job state · milestone · RFI)</li>
              <li>• PermitStream → /webhooks/permit (AHJ status changes)</li>
              <li>• Cyborg.ai → /webhooks/policy (alerts · kill-switch)</li>
              <li>• Audit chain → SSE /v1/audit/stream</li>
              <li>• Voice → WebSocket /v1/voice/session/{'{sessionId}'}</li>
            </ul>
          </Panel>

          <Panel title="Environment" subtitle="runtime configuration">
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <Env k="ENV" v="production" />
              <Env k="REGION" v="hetzner-fsn1" />
              <Env k="EDGE" v="cloudflare" />
              <Env k="ORCHESTRATOR" v="langgraph + temporal" />
              <Env k="DB" v="postgres-15 · pgvector" />
              <Env k="QUEUE" v="redis-streams + celery" />
              <Env k="ANCHOR" v="arbitrum-one · 30m batch" />
              <Env k="OBSERVABILITY" v="otel + grafana" />
            </dl>
          </Panel>

          <Panel title="Roadmap" subtitle="MVP phases">
            <ol className="list-decimal space-y-2 pl-5 text-sm text-ink-200">
              <li>
                <span className="font-semibold text-ink-100">Phase 1</span> — auth · revenue
                warboard · job pipeline · AI health <span className="pill-ok">live</span>
              </li>
              <li>
                <span className="font-semibold text-ink-100">Phase 2</span> — Stephanie avatar ·
                permit workflows · websocket live feeds <span className="pill-info">in flight</span>
              </li>
              <li>
                <span className="font-semibold text-ink-100">Phase 3</span> — DAO governance ·
                municipal APIs · AI automation controls <span className="pill-mute">queued</span>
              </li>
            </ol>
          </Panel>
        </div>
      </main>
    </>
  );
}

function Op({
  name,
  role,
  scope,
  mfa,
}: {
  name: string;
  role: string;
  scope: string;
  mfa?: boolean;
}) {
  return (
    <li className="flex items-center justify-between py-2">
      <div>
        <div className="num font-medium text-ink-100">{name}</div>
        <div className="text-[11px] text-ink-400">
          {role} · {scope}
        </div>
      </div>
      <span className={mfa ? 'pill-ok' : 'pill-warn'}>{mfa ? 'MFA' : 'no MFA'}</span>
    </li>
  );
}

function Integration({
  name,
  status,
  detail,
}: {
  name: string;
  status: 'connected' | 'degraded' | 'down';
  detail: string;
}) {
  const cls = status === 'connected' ? 'pill-ok' : status === 'degraded' ? 'pill-warn' : 'pill-err';
  return (
    <li className="flex items-center justify-between rounded-md border border-ink-700 bg-ink-900/50 px-3 py-2">
      <div>
        <div className="font-medium text-ink-100">{name}</div>
        <div className="text-[11px] text-ink-400">{detail}</div>
      </div>
      <span className={cls}>{status}</span>
    </li>
  );
}

function Coverage({
  label,
  status,
  detail,
}: {
  label: string;
  status: 'live' | 'mixed' | 'fixture';
  detail: string;
}) {
  const cls = status === 'live' ? 'pill-ok' : status === 'mixed' ? 'pill-warn' : 'pill-info';
  return (
    <li className="flex items-center justify-between rounded-md border border-ink-700 bg-ink-900/50 px-3 py-2">
      <div>
        <div className="font-medium text-ink-100">{label}</div>
        <div className="text-[11px] text-ink-400">{detail}</div>
      </div>
      <span className={cls}>{status}</span>
    </li>
  );
}

function Env({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-md border border-ink-700 bg-ink-900/50 px-3 py-2">
      <dt className="panel-subtitle">{k}</dt>
      <dd className="num text-ink-100">{v}</dd>
    </div>
  );
}
