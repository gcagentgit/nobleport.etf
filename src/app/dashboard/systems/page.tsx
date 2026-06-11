import { Topbar } from '@/components/dashboard/Topbar';
import { Panel } from '@/components/dashboard/Panel';
import { fetchSystemsRegistry } from '@/lib/dashboard/api';
import type { SystemNodeRow, TruthBucketKey } from '@/lib/dashboard/types';

export const dynamic = 'force-dynamic';

const BUCKET_LABEL: Record<TruthBucketKey, string> = {
  verified: 'Verified',
  staged: 'Staged',
  claimed: 'Claimed',
  demo: 'Demo / Simulation',
  planned: 'Planned',
  blocked: 'Blocked',
  legal_hold: 'Legal Hold',
  reference: 'Reference',
};

const BUCKET_PILL: Record<TruthBucketKey, string> = {
  verified: 'pill-ok',
  staged: 'pill-info',
  claimed: 'pill-warn',
  demo: 'pill-warn',
  planned: 'pill-mute',
  blocked: 'pill-err',
  legal_hold: 'pill-err',
  reference: 'pill-mute',
};

const BUCKET_ORDER: TruthBucketKey[] = [
  'verified',
  'staged',
  'claimed',
  'demo',
  'planned',
  'blocked',
  'legal_hold',
  'reference',
];

export default async function SystemsPage() {
  const reg = await fetchSystemsRegistry();
  const { summary } = reg;
  const grouped = BUCKET_ORDER.map((bucket) => ({
    bucket,
    nodes: reg.systems.filter((s) => s.bucket === bucket),
  })).filter((g) => g.nodes.length > 0);

  return (
    <>
      <Topbar pageTitle="Systems Truth Registry" generatedAt={reg.generatedAt} />
      <main className="flex-1 space-y-4 px-4 py-4 sm:px-6 sm:py-6">
        {/* Hard-truth banner */}
        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="pill-warn">HARD TRUTH</span>
            <span className="text-sm font-semibold text-amber-100">
              {summary.verified} / {summary.totalSystems} independently verified live
            </span>
          </div>
          <p className="mt-1.5 text-[12px] leading-relaxed text-amber-200/80">{reg.hardTruth}</p>
        </div>

        {/* Bucket summary tiles */}
        <section className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
          {BUCKET_ORDER.map((b) => (
            <div key={b} className="panel panel-pad">
              <div className="panel-subtitle">{BUCKET_LABEL[b]}</div>
              <div className="num mt-1.5 text-2xl font-semibold tracking-tight text-ink-50">
                {summary.byBucket[b] ?? 0}
              </div>
            </div>
          ))}
        </section>

        {/* Execution path */}
        <Panel title="Strongest Real Path" subtitle="execute in order · regulated layers last">
          <ol className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
            {reg.executionPath.map((p, i) => (
              <li key={p.step} className="rounded-md border border-ink-700 bg-ink-900/50 p-3">
                <div className="flex items-center gap-2">
                  <span className="num text-ink-500">{i + 1}.</span>
                  <span className="text-sm font-semibold text-ink-100">{p.step}</span>
                </div>
                <div className="mt-1 text-[11px] text-ink-400">{p.why}</div>
                <div className="mt-1 text-[10px] text-ink-500">{p.node}</div>
              </li>
            ))}
          </ol>
        </Panel>

        {/* Systems grouped by bucket */}
        {grouped.map(({ bucket, nodes }) => (
          <Panel
            key={bucket}
            title={BUCKET_LABEL[bucket]}
            subtitle={`${nodes.length} system${nodes.length === 1 ? '' : 's'} · ${reg.buckets.find((b) => b.bucket === bucket)?.promotionGate ?? ''}`}
            padded={false}
          >
            <table className="w-full text-sm">
              <thead className="bg-ink-900/80 text-[11px] uppercase tracking-wider text-ink-400">
                <tr>
                  <th className="px-4 py-2 text-left">System</th>
                  <th className="px-4 py-2 text-left">Category</th>
                  <th className="px-4 py-2 text-left">Evidence</th>
                  <th className="px-4 py-2 text-left">Next gate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-700">
                {nodes.map((n) => (
                  <SystemRow key={n.key} n={n} />
                ))}
              </tbody>
            </table>
          </Panel>
        ))}

        {/* Bucket definitions */}
        <Panel title="Truth Gates" subtitle="bucket definitions · promotion is evidence-first, never asserted">
          <ul className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {reg.buckets.map((b) => (
              <li key={b.bucket} className="rounded-md border border-ink-700 bg-ink-900/50 p-3">
                <div className="flex items-center justify-between">
                  <span className={BUCKET_PILL[b.bucket]}>{BUCKET_LABEL[b.bucket]}</span>
                  <span className="num text-[12px] text-ink-400">{b.count}</span>
                </div>
                <p className="mt-2 text-[12px] leading-relaxed text-ink-300">{b.definition}</p>
                <p className="mt-1 text-[11px] text-ink-500">Promote: {b.promotionGate}</p>
              </li>
            ))}
          </ul>
        </Panel>
      </main>
    </>
  );
}

function SystemRow({ n }: { n: SystemNodeRow }) {
  return (
    <tr className="row-hover align-top">
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="font-medium text-ink-100">{n.name}</span>
          {n.humanApprovalRequired && <span className="pill-warn text-[9px]">human-gated</span>}
        </div>
        <div className="text-[11px] text-ink-400">{n.summary}</div>
        <div className="mt-0.5 text-[10px] text-ink-500">
          {n.key} · {n.source}
        </div>
      </td>
      <td className="px-4 py-3">
        <span className="pill-mute">{n.category}</span>
      </td>
      <td className="px-4 py-3">
        <ul className="space-y-0.5 text-[11px] text-ink-300">
          {n.evidence.map((e) => (
            <li key={e} className="flex items-start gap-1">
              <span className="text-ink-600">·</span>
              {e}
            </li>
          ))}
        </ul>
      </td>
      <td className="px-4 py-3 text-[11px] text-ink-300">{n.nextGate}</td>
    </tr>
  );
}
