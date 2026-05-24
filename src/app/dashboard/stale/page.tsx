import { Topbar } from '@/components/dashboard/Topbar';
import { Panel } from '@/components/dashboard/Panel';
import { StatusPill } from '@/components/dashboard/StatusPill';

export const dynamic = 'force-dynamic';

const STALE = [
  {
    id: 'L-089',
    name: 'Margaret Donnelly',
    address: '44 High St, Newburyport',
    status: 'contacted',
    source: 'website',
    value: 210000,
    ageDays: 22,
    lastActivity: 'Email sent — no reply',
    agent: 'Agent-14',
  },
  {
    id: 'L-076',
    name: 'Victor Perez',
    address: '8 Central St, Gloucester',
    status: 'qualified',
    source: 'referral',
    value: 380000,
    ageDays: 18,
    lastActivity: 'Site visit scheduled — cancelled',
    agent: 'Agent-08',
  },
  {
    id: 'L-091',
    name: 'Helen O\'Rourke',
    address: '112 County Rd, Ipswich',
    status: 'new',
    source: 'social_media',
    value: 145000,
    ageDays: 31,
    lastActivity: 'Intake form submitted — never contacted',
    agent: null,
  },
  {
    id: 'L-065',
    name: 'David Park',
    address: '27 School St, Essex',
    status: 'qualified',
    source: 'partner',
    value: 520000,
    ageDays: 16,
    lastActivity: 'Estimate requested — not sent',
    agent: 'Agent-05',
  },
  {
    id: 'L-082',
    name: 'Karen Tseng',
    address: '3 Harbor Loop, Marblehead',
    status: 'contacted',
    source: 'website',
    value: 295000,
    ageDays: 25,
    lastActivity: 'Phone call — voicemail',
    agent: 'Agent-12',
  },
  {
    id: 'L-098',
    name: 'Brian Sullivan',
    address: '66 Summer St, Manchester-by-the-Sea',
    status: 'new',
    source: 'cold_call',
    value: 175000,
    ageDays: 42,
    lastActivity: 'Initial call — no follow-up',
    agent: null,
  },
];

function fmt(n: number) {
  return '$' + n.toLocaleString('en-US', { maximumFractionDigits: 0 });
}

export default function StalePage() {
  const now = new Date().toISOString();
  const totalValue = STALE.reduce((s, l) => s + l.value, 0);
  const unassigned = STALE.filter((l) => !l.agent).length;
  const critical = STALE.filter((l) => l.ageDays >= 30).length;

  return (
    <>
      <Topbar pageTitle="Stale Lead Detection" generatedAt={now} />
      <main className="flex-1 space-y-4 px-4 py-4 sm:px-6 sm:py-6">
        <div className="rounded-lg border border-red-500/30 bg-red-600/10 px-4 py-3">
          <div className="text-sm font-semibold text-red-200">
            {STALE.length} leads aged beyond 14-day threshold — {fmt(totalValue)} at risk
          </div>
          <div className="mt-1 text-xs text-red-300/80">
            {critical} critical (30+ days) · {unassigned} unassigned
          </div>
        </div>

        <Panel title="Stale Leads" subtitle="sorted by age · threshold 14 days">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-700 text-left text-[11px] uppercase tracking-wider text-ink-400">
                  <th className="pb-2 pr-3">Age</th>
                  <th className="pb-2 pr-3">Name</th>
                  <th className="pb-2 pr-3">Address</th>
                  <th className="pb-2 pr-3">Status</th>
                  <th className="pb-2 pr-3 text-right">Value</th>
                  <th className="pb-2 pr-3">Last Activity</th>
                  <th className="pb-2">Agent</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-800">
                {[...STALE].sort((a, b) => b.ageDays - a.ageDays).map((l) => (
                  <tr key={l.id} className="hover:bg-ink-900/40">
                    <td className="py-2 pr-3">
                      <span
                        className={`num rounded-full px-2 py-0.5 text-xs font-semibold ${
                          l.ageDays >= 30 ? 'bg-red-600/20 text-red-300 ring-1 ring-red-500/30' :
                          l.ageDays >= 21 ? 'bg-yellow-600/20 text-yellow-300 ring-1 ring-yellow-500/30' :
                          'bg-orange-600/20 text-orange-300 ring-1 ring-orange-500/30'
                        }`}
                      >
                        {l.ageDays}d
                      </span>
                    </td>
                    <td className="py-2 pr-3 font-medium text-ink-100">{l.name}</td>
                    <td className="py-2 pr-3 text-ink-200">{l.address}</td>
                    <td className="py-2 pr-3">
                      <StatusPill status="warn" label={l.status} />
                    </td>
                    <td className="py-2 pr-3 text-right num text-ink-100">{fmt(l.value)}</td>
                    <td className="py-2 pr-3 text-ink-300 max-w-[200px] truncate text-xs">{l.lastActivity}</td>
                    <td className="py-2 text-xs">
                      {l.agent ? (
                        <span className="text-ink-300">{l.agent}</span>
                      ) : (
                        <span className="text-red-400 font-semibold">unassigned</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Panel title="Aging Distribution" subtitle="days since last activity">
            <ul className="space-y-2 text-sm">
              {[
                { range: '14-21 days', count: 2, value: 900000 },
                { range: '22-30 days', count: 2, value: 505000 },
                { range: '30+ days', count: 2, value: 320000 },
              ].map((b) => (
                <li key={b.range} className="flex items-center justify-between rounded-md border border-ink-700 bg-ink-900/40 px-3 py-2">
                  <span className="text-ink-200">{b.range}</span>
                  <div className="flex gap-4 text-xs">
                    <span className="num text-ink-100">{b.count} leads</span>
                    <span className="num text-red-300">{fmt(b.value)} at risk</span>
                  </div>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title="Recovery Actions" subtitle="recommended next steps">
            <ul className="space-y-2 text-sm">
              <li className="rounded-md border border-yellow-500/20 bg-yellow-600/10 px-3 py-2 text-yellow-200">
                Re-assign {unassigned} unassigned leads to available agents
              </li>
              <li className="rounded-md border border-yellow-500/20 bg-yellow-600/10 px-3 py-2 text-yellow-200">
                Schedule follow-up calls for {STALE.filter(l => l.status === 'contacted').length} contacted leads
              </li>
              <li className="rounded-md border border-red-500/20 bg-red-600/10 px-3 py-2 text-red-200">
                Escalate {critical} critical leads (30+ days) to sales manager
              </li>
              <li className="rounded-md border border-ink-700 bg-ink-900/40 px-3 py-2 text-ink-200">
                Review agent performance for stale lead patterns
              </li>
            </ul>
          </Panel>
        </div>
      </main>
    </>
  );
}
