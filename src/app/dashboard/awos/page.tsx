import { Topbar } from '@/components/dashboard/Topbar';
import { Panel } from '@/components/dashboard/Panel';
import { StatusPill } from '@/components/dashboard/StatusPill';

export const dynamic = 'force-dynamic';

const AWOS = [
  {
    id: 'JOB-0012-CO-01',
    job: 'NP-204',
    title: 'Upgrade to spray foam insulation',
    reason: 'client_request',
    status: 'approved',
    laborCost: 4200,
    materialCost: 3100,
    markup: 25,
    total: 9125,
    scheduleDays: 2,
    approvedBy: 'Mike O.',
    aiSuggested: true,
  },
  {
    id: 'JOB-0015-CO-01',
    job: 'NP-211',
    title: 'Relocate HVAC ductwork — site condition',
    reason: 'site_condition',
    status: 'in_progress',
    laborCost: 6800,
    materialCost: 2400,
    markup: 20,
    total: 11040,
    scheduleDays: 4,
    approvedBy: 'Mike O.',
    aiSuggested: false,
  },
  {
    id: 'JOB-0015-CO-02',
    job: 'NP-211',
    title: 'Code-required fire stopping at penetrations',
    reason: 'code_requirement',
    status: 'proposed',
    laborCost: 1800,
    materialCost: 650,
    markup: 30,
    total: 3185,
    scheduleDays: 1,
    approvedBy: null,
    aiSuggested: true,
  },
  {
    id: 'JOB-0018-CO-01',
    job: 'NP-220',
    title: 'Client upgrade: quartz countertops',
    reason: 'design_change',
    status: 'sent',
    laborCost: 1200,
    materialCost: 4800,
    markup: 15,
    total: 6900,
    scheduleDays: 0,
    approvedBy: null,
    aiSuggested: false,
  },
  {
    id: 'JOB-0020-CO-01',
    job: 'NP-225',
    title: 'Foundation drain tile — unexpected ledge',
    reason: 'site_condition',
    status: 'draft',
    laborCost: 8500,
    materialCost: 3200,
    markup: 25,
    total: 14625,
    scheduleDays: 3,
    approvedBy: null,
    aiSuggested: true,
  },
];

const STATUS_TONE: Record<string, 'ok' | 'warn' | 'err' | 'info' | 'muted'> = {
  draft: 'muted',
  proposed: 'info',
  sent: 'info',
  approved: 'ok',
  in_progress: 'ok',
  completed: 'ok',
  rejected: 'err',
  voided: 'muted',
};

function fmt(n: number) {
  return '$' + n.toLocaleString('en-US', { maximumFractionDigits: 0 });
}

export default function AWOsPage() {
  const now = new Date().toISOString();
  const totalValue = AWOS.reduce((s, a) => s + a.total, 0);
  const approvedValue = AWOS.filter((a) => ['approved', 'in_progress', 'completed'].includes(a.status)).reduce((s, a) => s + a.total, 0);
  const pendingValue = AWOS.filter((a) => ['draft', 'proposed', 'sent'].includes(a.status)).reduce((s, a) => s + a.total, 0);
  const aiCount = AWOS.filter((a) => a.aiSuggested).length;

  return (
    <>
      <Topbar pageTitle="AWO Ledger" generatedAt={now} />
      <main className="flex-1 space-y-4 px-4 py-4 sm:px-6 sm:py-6">
        <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <MiniKpi label="Total AWOs" value={AWOS.length} />
          <MiniKpi label="Total Value" value={fmt(totalValue)} />
          <MiniKpi label="Approved" value={fmt(approvedValue)} tone="ok" />
          <MiniKpi label="Pending" value={fmt(pendingValue)} tone="warn" />
        </section>

        <Panel
          title="Change Order Ledger"
          subtitle={`${AWOS.length} AWOs · ${aiCount} AI-suggested`}
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-700 text-left text-[11px] uppercase tracking-wider text-ink-400">
                  <th className="pb-2 pr-3">CO #</th>
                  <th className="pb-2 pr-3">Job</th>
                  <th className="pb-2 pr-3">Title</th>
                  <th className="pb-2 pr-3">Reason</th>
                  <th className="pb-2 pr-3">Status</th>
                  <th className="pb-2 pr-3 text-right">Labor</th>
                  <th className="pb-2 pr-3 text-right">Material</th>
                  <th className="pb-2 pr-3 text-right">Markup</th>
                  <th className="pb-2 pr-3 text-right">Total</th>
                  <th className="pb-2 pr-3 text-right">Days</th>
                  <th className="pb-2">AI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-800">
                {AWOS.map((a) => (
                  <tr key={a.id} className="hover:bg-ink-900/40">
                    <td className="py-2 pr-3 font-mono text-xs text-violet-300">{a.id}</td>
                    <td className="py-2 pr-3 font-medium text-ink-100">{a.job}</td>
                    <td className="py-2 pr-3 text-ink-200 max-w-[220px] truncate">{a.title}</td>
                    <td className="py-2 pr-3 text-ink-300 text-xs">{a.reason.replace('_', ' ')}</td>
                    <td className="py-2 pr-3">
                      <StatusPill status={STATUS_TONE[a.status] ?? 'muted'} label={a.status.replace('_', ' ')} />
                    </td>
                    <td className="py-2 pr-3 text-right num text-ink-200">{fmt(a.laborCost)}</td>
                    <td className="py-2 pr-3 text-right num text-ink-200">{fmt(a.materialCost)}</td>
                    <td className="py-2 pr-3 text-right num text-ink-300">{a.markup}%</td>
                    <td className="py-2 pr-3 text-right num font-semibold text-ink-100">{fmt(a.total)}</td>
                    <td className={`py-2 pr-3 text-right num ${a.scheduleDays > 0 ? 'text-yellow-300' : 'text-ink-400'}`}>
                      {a.scheduleDays > 0 ? `+${a.scheduleDays}` : '--'}
                    </td>
                    <td className="py-2">
                      {a.aiSuggested && (
                        <span className="rounded-full bg-violet-600/20 px-2 py-0.5 text-[10px] font-semibold text-violet-300 ring-1 ring-violet-500/30">
                          AI
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Panel title="AWO Revenue Impact" subtitle="margin recovery analysis">
            <ul className="space-y-2 text-sm">
              <li className="flex justify-between"><span className="text-ink-300">Avg markup</span><span className="num font-semibold text-ink-100">23%</span></li>
              <li className="flex justify-between"><span className="text-ink-300">Total schedule impact</span><span className="num text-yellow-300">+10 days</span></li>
              <li className="flex justify-between"><span className="text-ink-300">AI-suggested recovery</span><span className="num text-emerald-300">{fmt(AWOS.filter(a => a.aiSuggested).reduce((s, a) => s + a.total, 0))}</span></li>
              <li className="flex justify-between"><span className="text-ink-300">Approval rate</span><span className="num text-ink-100">80%</span></li>
            </ul>
          </Panel>
          <Panel title="Reason Distribution" subtitle="why AWOs happen">
            <ul className="space-y-2 text-sm">
              {['client_request', 'site_condition', 'code_requirement', 'design_change'].map((r) => {
                const count = AWOS.filter((a) => a.reason === r).length;
                return (
                  <li key={r} className="flex items-center justify-between rounded-md border border-ink-700 bg-ink-900/40 px-3 py-2">
                    <span className="text-ink-200">{r.replace(/_/g, ' ')}</span>
                    <span className="num text-ink-100">{count}</span>
                  </li>
                );
              })}
            </ul>
          </Panel>
        </div>
      </main>
    </>
  );
}

function MiniKpi({
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
      <div className={`num mt-1 text-xl font-semibold ${cls}`}>{value}</div>
    </div>
  );
}
