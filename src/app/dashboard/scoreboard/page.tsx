import { Topbar } from '@/components/dashboard/Topbar';
import { Panel } from '@/components/dashboard/Panel';

export const dynamic = 'force-dynamic';

function fmt(n: number) {
  return '$' + n.toLocaleString('en-US', { maximumFractionDigits: 0 });
}

function pct(n: number) {
  return (n * 100).toFixed(1) + '%';
}

const AGENTS = [
  { rank: 1, name: 'Agent-03', leads: 48, inspections: 22, closeRate: 0.42, revenue: 1_240_000, stalePct: 0.06 },
  { rank: 2, name: 'Agent-07', leads: 41, inspections: 18, closeRate: 0.38, revenue: 980_000, stalePct: 0.09 },
  { rank: 3, name: 'Agent-12', leads: 39, inspections: 15, closeRate: 0.31, revenue: 720_000, stalePct: 0.12 },
  { rank: 4, name: 'Agent-01', leads: 36, inspections: 14, closeRate: 0.29, revenue: 680_000, stalePct: 0.14 },
  { rank: 5, name: 'Agent-19', leads: 34, inspections: 12, closeRate: 0.27, revenue: 590_000, stalePct: 0.15 },
  { rank: 6, name: 'Agent-05', leads: 32, inspections: 11, closeRate: 0.25, revenue: 510_000, stalePct: 0.18 },
  { rank: 7, name: 'Agent-14', leads: 30, inspections: 10, closeRate: 0.23, revenue: 470_000, stalePct: 0.20 },
  { rank: 8, name: 'Agent-08', leads: 28, inspections: 9, closeRate: 0.22, revenue: 420_000, stalePct: 0.22 },
];

const PIPELINE_STATS = {
  totalLeads: 310,
  inspectionsBooked: 124,
  estimatesSent: 88,
  won: 41,
  lost: 22,
  winRate: 0.651,
  avgDealSize: 284_000,
  pipelineValue: 18_400_000,
};

export default function ScoreboardPage() {
  const now = new Date().toISOString();

  return (
    <>
      <Topbar pageTitle="Trust Pipeline Scoreboard" generatedAt={now} />
      <main className="flex-1 space-y-4 px-4 py-4 sm:px-6 sm:py-6">
        <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <KpiBox label="Total Leads (MTD)" value={PIPELINE_STATS.totalLeads} />
          <KpiBox label="Inspections Booked" value={PIPELINE_STATS.inspectionsBooked} />
          <KpiBox label="Win Rate" value={pct(PIPELINE_STATS.winRate)} tone="ok" />
          <KpiBox label="Pipeline Value" value={fmt(PIPELINE_STATS.pipelineValue)} />
        </section>

        <Panel title="Agent Leaderboard" subtitle="20-agent lead contest · ranked by revenue">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-700 text-left text-[11px] uppercase tracking-wider text-ink-400">
                  <th className="pb-2 pr-3 w-10">#</th>
                  <th className="pb-2 pr-3">Agent</th>
                  <th className="pb-2 pr-3 text-right">Leads</th>
                  <th className="pb-2 pr-3 text-right">Inspections</th>
                  <th className="pb-2 pr-3 text-right">Close Rate</th>
                  <th className="pb-2 pr-3 text-right">Revenue</th>
                  <th className="pb-2 text-right">Stale %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-800">
                {AGENTS.map((a) => (
                  <tr key={a.name} className="hover:bg-ink-900/40">
                    <td className="py-2 pr-3">
                      <span className={`num font-bold ${a.rank <= 3 ? 'text-yellow-300' : 'text-ink-400'}`}>
                        {a.rank}
                      </span>
                    </td>
                    <td className="py-2 pr-3 font-medium text-violet-300">{a.name}</td>
                    <td className="py-2 pr-3 text-right num text-ink-100">{a.leads}</td>
                    <td className="py-2 pr-3 text-right num text-ink-100">{a.inspections}</td>
                    <td className={`py-2 pr-3 text-right num ${a.closeRate >= 0.35 ? 'text-emerald-300' : a.closeRate >= 0.25 ? 'text-yellow-300' : 'text-red-300'}`}>
                      {pct(a.closeRate)}
                    </td>
                    <td className="py-2 pr-3 text-right num font-semibold text-ink-100">{fmt(a.revenue)}</td>
                    <td className={`py-2 text-right num ${a.stalePct > 0.15 ? 'text-red-300' : 'text-ink-300'}`}>
                      {pct(a.stalePct)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Panel title="Conversion Funnel" subtitle="Lead → Close">
            <ul className="space-y-2 text-sm">
              {[
                { stage: 'Lead → Inspection', rate: 0.40, count: 124 },
                { stage: 'Inspection → Estimate', rate: 0.71, count: 88 },
                { stage: 'Estimate → Won', rate: 0.47, count: 41 },
                { stage: 'Overall Conversion', rate: 0.132, count: 41 },
              ].map((s) => (
                <li key={s.stage} className="flex items-center justify-between rounded-md border border-ink-700 bg-ink-900/40 px-3 py-2">
                  <span className="text-ink-200">{s.stage}</span>
                  <div className="flex gap-3 text-xs">
                    <span className="num text-ink-100">{s.count}</span>
                    <span className={`num font-semibold ${s.rate >= 0.4 ? 'text-emerald-300' : s.rate >= 0.2 ? 'text-yellow-300' : 'text-red-300'}`}>
                      {pct(s.rate)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title="Market Performance" subtitle="revenue by target market">
            <ul className="space-y-2 text-sm">
              {[
                { market: 'Newburyport', revenue: 6_200_000 },
                { market: 'Ipswich', revenue: 3_100_000 },
                { market: 'Marblehead', revenue: 4_800_000 },
                { market: 'Manchester-by-the-Sea', revenue: 2_900_000 },
                { market: 'Essex', revenue: 1_400_000 },
              ].map((m) => (
                <li key={m.market} className="flex items-center justify-between rounded-md border border-ink-700 bg-ink-900/40 px-3 py-2">
                  <span className="text-ink-200">{m.market}</span>
                  <span className="num font-semibold text-ink-100">{fmt(m.revenue)}</span>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title="Key Metrics" subtitle="operational health">
            <ul className="space-y-2 text-sm">
              <li className="flex justify-between"><span className="text-ink-300">Avg deal size</span><span className="num text-ink-100">{fmt(PIPELINE_STATS.avgDealSize)}</span></li>
              <li className="flex justify-between"><span className="text-ink-300">Won deals (MTD)</span><span className="num text-emerald-300">{PIPELINE_STATS.won}</span></li>
              <li className="flex justify-between"><span className="text-ink-300">Lost deals (MTD)</span><span className="num text-red-300">{PIPELINE_STATS.lost}</span></li>
              <li className="flex justify-between"><span className="text-ink-300">Estimates sent</span><span className="num text-ink-100">{PIPELINE_STATS.estimatesSent}</span></li>
              <li className="flex justify-between"><span className="text-ink-300">Avg response time</span><span className="num text-ink-100">4.2h</span></li>
            </ul>
          </Panel>
        </div>
      </main>
    </>
  );
}

function KpiBox({
  label,
  value,
  tone = 'info',
}: {
  label: string;
  value: number | string;
  tone?: 'ok' | 'warn' | 'err' | 'info';
}) {
  const cls =
    tone === 'ok' ? 'text-emerald-300' : tone === 'warn' ? 'text-yellow-300' : tone === 'err' ? 'text-red-300' : 'text-blue-300';
  return (
    <div className="rounded-md border border-ink-700 bg-ink-900/50 p-3">
      <div className="text-[11px] uppercase tracking-wider text-ink-400">{label}</div>
      <div className={`num mt-1 text-2xl font-semibold ${cls}`}>{value}</div>
    </div>
  );
}
