import Link from 'next/link';
import { Topbar } from '@/components/dashboard/Topbar';
import { RoofingTabs } from '@/components/dashboard/RoofingTabs';
import { roofingProposals } from '@/lib/roofing/proposals';
import { fmtUSD } from '@/lib/dashboard/format';

export const dynamic = 'force-dynamic';

const STATUS_CLASS: Record<string, string> = {
  draft: 'pill-warn',
  sent: 'pill-info',
  accepted: 'pill-ok',
  declined: 'pill-err',
};

export default function RoofingProposalsIndexPage() {
  const pipeline = roofingProposals.reduce((s, p) => s + p.total, 0);

  return (
    <>
      <Topbar pageTitle="NoblePort Roofing · Proposals" />
      <RoofingTabs />
      <main className="flex-1 space-y-4 px-4 py-4 sm:px-6 sm:py-6">
        <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Stat label="Open Proposals" value={String(roofingProposals.length)} />
          <Stat label="Pipeline Value" value={fmtUSD(pipeline)} tone="ok" />
          <Stat
            label="Draft"
            value={String(roofingProposals.filter((p) => p.status === 'draft').length)}
            tone="warn"
          />
          <Stat
            label="Accepted"
            value={String(roofingProposals.filter((p) => p.status === 'accepted').length)}
          />
        </section>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {roofingProposals.map((p) => (
            <Link
              key={p.id}
              href={`/dashboard/roofing/proposals/${p.id}`}
              className="group panel panel-pad transition-colors hover:bg-ink-800/40"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="panel-subtitle">{p.company}</div>
                  <h3 className="mt-1 text-base font-semibold text-ink-50 group-hover:text-violet-100">
                    {p.projectAddress}
                  </h3>
                  <p className="text-[12px] text-ink-400">
                    <span className="num">{p.proposalNo}</span> · {p.date}
                  </p>
                </div>
                <span className={STATUS_CLASS[p.status]}>{p.status.toUpperCase()}</span>
              </div>

              {p.summary && (
                <p className="mt-2 line-clamp-2 text-[12px] leading-relaxed text-ink-300">{p.summary}</p>
              )}

              <div className="mt-3 grid grid-cols-3 gap-2 border-t border-ink-700 pt-3">
                <Mini label="Area" value={`${p.totalAreaSf.toLocaleString()} SF`} hint={`${p.pitch} pitch`} />
                <Mini label="Total" value={fmtUSD(p.total)} hint="est." tone="ok" />
                <Mini
                  label="Range"
                  value={`${fmtUSD(p.investmentLow)}–${fmtUSD(p.investmentHigh)}`}
                  hint="w/ contingency"
                />
              </div>

              <div className="mt-3 text-[12px] font-medium text-violet-300 group-hover:text-violet-200">
                View proposal →
              </div>
            </Link>
          ))}
        </div>

        <p className="px-1 text-[11px] leading-relaxed text-ink-500">
          Proposals are internal estimates resolved from field measurements at NoblePort unit rates. Figures are not a
          firm bid until on-site deck inspection and signature.
        </p>
      </main>
    </>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: 'ok' | 'warn' | 'err' }) {
  const toneCls =
    tone === 'ok'
      ? 'text-emerald-300'
      : tone === 'warn'
        ? 'text-yellow-300'
        : tone === 'err'
          ? 'text-red-300'
          : 'text-ink-50';
  return (
    <div className="panel panel-pad">
      <div className="panel-subtitle">{label}</div>
      <div className={`num mt-1.5 text-xl font-semibold tracking-tight ${toneCls}`}>{value}</div>
    </div>
  );
}

function Mini({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: 'ok';
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-ink-500">{label}</div>
      <div className={`num text-[13px] font-semibold ${tone === 'ok' ? 'text-emerald-300' : 'text-ink-100'}`}>
        {value}
      </div>
      {hint && <div className="text-[10px] text-ink-500">{hint}</div>}
    </div>
  );
}
