import { Topbar } from '@/components/dashboard/Topbar';
import { Panel } from '@/components/dashboard/Panel';
import { StatusPill } from '@/components/dashboard/StatusPill';

export const dynamic = 'force-dynamic';

const LEADS = [
  {
    id: 'L-001',
    name: 'Sarah Whitfield',
    source: 'website',
    status: 'new',
    address: '15 Federal St, Newburyport',
    value: 185000,
    ageHours: 2,
    assigned: null,
    score: 92,
  },
  {
    id: 'L-002',
    name: 'James Chen',
    source: 'referral',
    status: 'contacted',
    address: '88 Granite St, Rockport',
    value: 320000,
    ageHours: 18,
    assigned: 'Agent-07',
    score: 87,
  },
  {
    id: 'L-003',
    name: 'Patricia Navarro',
    source: 'social_media',
    status: 'new',
    address: '5 Ocean Ave, Marblehead',
    value: 450000,
    ageHours: 1,
    assigned: null,
    score: 95,
  },
  {
    id: 'L-004',
    name: 'Robert Healey',
    source: 'website',
    status: 'qualified',
    address: '221 Main St, Essex',
    value: 95000,
    ageHours: 48,
    assigned: 'Agent-12',
    score: 68,
  },
  {
    id: 'L-005',
    name: 'Diana Kowalski',
    source: 'referral',
    status: 'new',
    address: '34 Spring St, Ipswich',
    value: 275000,
    ageHours: 5,
    assigned: null,
    score: 88,
  },
  {
    id: 'L-006',
    name: 'Thomas Burke',
    source: 'partner',
    status: 'contacted',
    address: '12 Beach Rd, Manchester-by-the-Sea',
    value: 525000,
    ageHours: 72,
    assigned: 'Agent-03',
    score: 91,
  },
];

const STATUS_TONE: Record<string, 'ok' | 'warn' | 'info' | 'muted'> = {
  new: 'info',
  contacted: 'warn',
  qualified: 'ok',
};

function fmt(n: number) {
  return '$' + n.toLocaleString('en-US', { maximumFractionDigits: 0 });
}

export default function IntakePage() {
  const now = new Date().toISOString();
  const totalValue = LEADS.reduce((s, l) => s + l.value, 0);
  const unassigned = LEADS.filter((l) => !l.assigned).length;
  const premium = LEADS.filter((l) => l.score >= 85).length;

  return (
    <>
      <Topbar pageTitle="Lead Intake" generatedAt={now} />
      <main className="flex-1 space-y-4 px-4 py-4 sm:px-6 sm:py-6">
        <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Stat label="Queue" value={LEADS.length} />
          <Stat label="Pipeline Value" value={fmt(totalValue)} />
          <Stat label="Unassigned" value={unassigned} tone="warn" />
          <Stat label="Premium Leads" value={premium} tone="ok" />
        </section>

        <Panel title="Intake Queue" subtitle="sorted by homeowner score">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-700 text-left text-[11px] uppercase tracking-wider text-ink-400">
                  <th className="pb-2 pr-3">Score</th>
                  <th className="pb-2 pr-3">Name</th>
                  <th className="pb-2 pr-3">Address</th>
                  <th className="pb-2 pr-3">Source</th>
                  <th className="pb-2 pr-3">Status</th>
                  <th className="pb-2 pr-3 text-right">Est. Value</th>
                  <th className="pb-2 pr-3 text-right">Age</th>
                  <th className="pb-2">Agent</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-800">
                {[...LEADS].sort((a, b) => b.score - a.score).map((l) => (
                  <tr key={l.id} className="hover:bg-ink-900/40">
                    <td className="py-2 pr-3">
                      <span
                        className={`num rounded-full px-2 py-0.5 text-xs font-semibold ${
                          l.score >= 85 ? 'bg-emerald-600/20 text-emerald-300 ring-1 ring-emerald-500/30' :
                          l.score >= 60 ? 'bg-yellow-600/20 text-yellow-300 ring-1 ring-yellow-500/30' :
                          'bg-ink-700/50 text-ink-300'
                        }`}
                      >
                        {l.score}
                      </span>
                    </td>
                    <td className="py-2 pr-3 font-medium text-ink-100">{l.name}</td>
                    <td className="py-2 pr-3 text-ink-200">{l.address}</td>
                    <td className="py-2 pr-3 text-ink-300 text-xs">{l.source}</td>
                    <td className="py-2 pr-3">
                      <StatusPill status={STATUS_TONE[l.status] ?? 'muted'} label={l.status} />
                    </td>
                    <td className="py-2 pr-3 text-right num text-ink-100">{fmt(l.value)}</td>
                    <td className={`py-2 pr-3 text-right num ${l.ageHours > 24 ? 'text-yellow-300' : 'text-ink-300'}`}>
                      {l.ageHours >= 24 ? `${Math.floor(l.ageHours / 24)}d` : `${l.ageHours}h`}
                    </td>
                    <td className="py-2 text-ink-300 text-xs">
                      {l.assigned ?? <span className="text-yellow-400">unassigned</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Market Distribution" subtitle="leads by target market">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {[
              { market: 'Newburyport', count: 1, value: 185000 },
              { market: 'Ipswich', count: 1, value: 275000 },
              { market: 'Essex', count: 1, value: 95000 },
              { market: 'Manchester-by-the-Sea', count: 1, value: 525000 },
              { market: 'Marblehead', count: 1, value: 450000 },
            ].map((m) => (
              <div key={m.market} className="rounded-md border border-ink-700 bg-ink-900/40 p-3">
                <div className="text-xs font-medium text-ink-100">{m.market}</div>
                <div className="num mt-1 text-lg font-semibold text-violet-300">{m.count}</div>
                <div className="text-[11px] text-ink-400">{fmt(m.value)}</div>
              </div>
            ))}
          </div>
        </Panel>
      </main>
    </>
  );
}

function Stat({
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
