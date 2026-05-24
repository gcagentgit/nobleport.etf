import { Topbar } from '@/components/dashboard/Topbar';
import { Panel } from '@/components/dashboard/Panel';

export const dynamic = 'force-dynamic';

export default function TypologyPage() {
  const now = new Date().toISOString();

  return (
    <>
      <Topbar pageTitle="Typology Intelligence" generatedAt={now} />
      <main className="flex-1 space-y-6 px-4 py-4 sm:px-6 sm:py-6">
        <div className="rounded-lg border border-violet-500/20 bg-violet-600/5 p-4">
          <h2 className="text-sm font-semibold text-violet-200">Structured Classification Engine</h2>
          <p className="mt-1 text-xs text-ink-300">
            Sits between AI reasoning and deterministic operational execution.
            Prevents hallucinated categories, normalizes operational data,
            and provides measurable classification intelligence.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <Panel title="Customer Archetypes" subtitle="12 canonical client types">
            <div className="space-y-2">
              {ARCHETYPES.map((a) => (
                <div key={a.type} className="flex items-center justify-between rounded border border-ink-700/50 px-3 py-2">
                  <div>
                    <span className="text-sm font-medium text-ink-100">{a.label}</span>
                    <span className="ml-2 text-[11px] text-ink-400">{a.type}</span>
                  </div>
                  <div className="flex gap-3 text-[11px]">
                    <span className={revColor(a.revenue)}>{a.revenue}</span>
                    <span className={riskColor(a.permitRisk)}>{a.permitRisk} risk</span>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Project Taxonomy" subtitle="Hierarchical classification">
            <div className="font-mono text-xs text-ink-200 space-y-0.5">
              <TaxLine depth={0} label="Project" />
              <TaxLine depth={1} label="Residential" />
              <TaxLine depth={2} label="Renovation" />
              <TaxLine depth={2} label="Addition" />
              <TaxLine depth={2} label="New Construction" />
              <TaxLine depth={2} label="Historic Renovation" />
              <TaxLine depth={2} label="Coastal Build" />
              <TaxLine depth={1} label="Commercial" />
              <TaxLine depth={2} label="Tenant Fit-Out" />
              <TaxLine depth={2} label="Ground-Up" />
              <TaxLine depth={2} label="Adaptive Reuse" />
              <TaxLine depth={1} label="Municipal" />
              <TaxLine depth={2} label="Civic Buildings" />
              <TaxLine depth={2} label="Infrastructure" />
              <TaxLine depth={1} label="Maintenance" />
              <TaxLine depth={2} label="Scheduled" />
              <TaxLine depth={2} label="Emergency" />
              <TaxLine depth={2} label="Warranty" />
            </div>
          </Panel>

          <Panel title="Operational Entropy" subtitle="Business predictability metric">
            <div className="space-y-4">
              <div className="flex items-baseline gap-3">
                <span className="num text-3xl font-semibold text-amber-300">0.72</span>
                <span className="text-xs text-ink-400">normalized (0–1)</span>
              </div>
              <p className="text-xs text-ink-300">
                Moderate-high entropy — diverse intake mix. Monitor for instability.
                Dominant type: residential_renovation (34%).
              </p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <EntropyBar label="Reno" pct={34} />
                <EntropyBar label="Addition" pct={20} />
                <EntropyBar label="Maintenance" pct={15} />
                <EntropyBar label="Commercial" pct={12} />
              </div>
            </div>
          </Panel>

          <Panel title="Coverage Gaps" subtitle="Operational blind spots">
            <div className="space-y-2">
              <GapRow type="multi_family_developer" count={0} severity="critical" />
              <GapRow type="investor_flip" count={0} severity="critical" />
              <GapRow type="insurance_restoration" count={0} severity="critical" />
              <p className="mt-3 text-[11px] text-ink-400">
                3 customer archetypes have zero representation this period.
                Coverage: 75% (9/12 types active).
              </p>
            </div>
          </Panel>

          <Panel title="Category Normalization" subtitle="Fuzzy → Canonical mapping">
            <div className="space-y-1.5 text-xs">
              <NormRow inputs={['VIP Client', 'Luxury Client', 'Premium Client']} canonical="HIGH_VALUE_CLIENT" />
              <NormRow inputs={['Reno', 'Remodel', 'Rehab']} canonical="RENOVATION" />
              <NormRow inputs={['In Review', 'Plan Review', 'Examiner Assigned']} canonical="IN_REVIEW" />
              <NormRow inputs={['Emergency', 'Rush', 'ASAP']} canonical="EMERGENCY_CLIENT" />
            </div>
          </Panel>

          <Panel title="Lifecycle Transitions" subtitle="Stage conversion rates">
            <div className="space-y-2 text-xs">
              <TransRow from="Lead" to="Intake" pct={68} />
              <TransRow from="Intake" to="Estimate" pct={82} />
              <TransRow from="Estimate" to="Permit" pct={41} />
              <TransRow from="Permit" to="Build" pct={94} />
              <TransRow from="Build" to="Invoice" pct={97} />
              <TransRow from="Invoice" to="Closeout" pct={88} />
              <TransRow from="Closeout" to="Maintenance" pct={23} />
            </div>
          </Panel>
        </div>
      </main>
    </>
  );
}

// ─── Data ─────────────────────────────────────────────────────────────────────

const ARCHETYPES = [
  { type: 'luxury_renovation', label: 'Luxury Renovation', revenue: 'High', permitRisk: 'Medium' },
  { type: 'emergency_repair', label: 'Emergency Repair', revenue: 'Fast', permitRisk: 'Low' },
  { type: 'historic_property', label: 'Historic Property', revenue: 'Medium', permitRisk: 'High' },
  { type: 'coastal_build', label: 'Coastal Build', revenue: 'High', permitRisk: 'High' },
  { type: 'commercial_tenant_fit', label: 'Commercial Fit-Out', revenue: 'Institutional', permitRisk: 'Medium' },
  { type: 'multi_family_developer', label: 'Multi-Family Developer', revenue: 'High', permitRisk: 'High' },
  { type: 'municipal_project', label: 'Municipal Project', revenue: 'Institutional', permitRisk: 'Medium' },
  { type: 'repeat_maintenance', label: 'Repeat Maintenance', revenue: 'Recurring', permitRisk: 'Low' },
  { type: 'investor_flip', label: 'Investor Flip', revenue: 'Fast', permitRisk: 'Low' },
  { type: 'first_time_homeowner', label: 'First-Time Homeowner', revenue: 'Medium', permitRisk: 'Low' },
  { type: 'insurance_restoration', label: 'Insurance Restoration', revenue: 'Fast', permitRisk: 'Low' },
  { type: 'adaptive_reuse', label: 'Adaptive Reuse', revenue: 'High', permitRisk: 'Extreme' },
];

// ─── Sub-components ───────────────────────────────────────────────────────────

function revColor(rev: string) {
  if (rev === 'High' || rev === 'Institutional') return 'text-emerald-300';
  if (rev === 'Fast') return 'text-blue-300';
  if (rev === 'Recurring') return 'text-violet-300';
  return 'text-ink-300';
}

function riskColor(risk: string) {
  if (risk === 'Extreme') return 'text-red-300';
  if (risk === 'High') return 'text-amber-300';
  if (risk === 'Medium') return 'text-yellow-300';
  return 'text-emerald-300';
}

function TaxLine({ depth, label }: { depth: number; label: string }) {
  const indent = depth * 20;
  const prefix = depth === 0 ? '' : depth === 1 ? '├── ' : '│   ├── ';
  return (
    <div style={{ paddingLeft: `${indent}px` }}>
      <span className="text-ink-500">{prefix}</span>
      <span className="text-ink-100">{label}</span>
    </div>
  );
}

function EntropyBar({ label, pct }: { label: string; pct: number }) {
  return (
    <div>
      <div className="flex justify-between text-[10px] text-ink-400">
        <span>{label}</span>
        <span className="num">{pct}%</span>
      </div>
      <div className="mt-0.5 h-1.5 w-full rounded-full bg-ink-800">
        <div className="h-full rounded-full bg-violet-500" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function GapRow({ type, count, severity }: { type: string; count: number; severity: string }) {
  return (
    <div className="flex items-center justify-between rounded border border-red-500/20 bg-red-500/5 px-3 py-2">
      <span className="text-sm text-ink-200">{type}</span>
      <div className="flex items-center gap-2">
        <span className="num text-xs text-red-300">count: {count}</span>
        <span className="rounded bg-red-500/20 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-red-300">
          {severity}
        </span>
      </div>
    </div>
  );
}

function NormRow({ inputs, canonical }: { inputs: string[]; canonical: string }) {
  return (
    <div className="flex items-center gap-2 rounded border border-ink-700/50 px-3 py-2">
      <div className="flex-1 text-ink-400">
        {inputs.map((i, idx) => (
          <span key={i}>
            {idx > 0 && <span className="text-ink-600"> / </span>}
            <span className="italic">{i}</span>
          </span>
        ))}
      </div>
      <span className="text-ink-600">→</span>
      <span className="font-mono font-semibold text-emerald-300">{canonical}</span>
    </div>
  );
}

function TransRow({ from, to, pct }: { from: string; to: string; pct: number }) {
  const color = pct >= 80 ? 'text-emerald-300' : pct >= 50 ? 'text-amber-300' : 'text-red-300';
  return (
    <div className="flex items-center justify-between">
      <span className="text-ink-300">
        {from} <span className="text-ink-600">→</span> {to}
      </span>
      <span className={`num font-semibold ${color}`}>{pct}%</span>
    </div>
  );
}
