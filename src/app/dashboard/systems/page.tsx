import { Topbar } from '@/components/dashboard/Topbar';
import { Panel } from '@/components/dashboard/Panel';
import { DeploymentPill, HealthPill } from '@/components/dashboard/StatusPill';
import {
  LAYER_DEFINITIONS,
  SYSTEM_MODULES,
  getModulesByLayer,
  getStatusCounts,
  type OperationalLayer,
  type ModuleStatus,
} from '@/lib/dashboard/typology';
import type { DeploymentBadge } from '@/lib/dashboard/types';

export const dynamic = 'force-dynamic';

export default function SystemsPage() {
  const counts = getStatusCounts();
  const now = new Date().toISOString();

  return (
    <>
      <Topbar pageTitle="System Typology" generatedAt={now} />
      <main className="flex-1 space-y-6 px-4 py-4 sm:px-6 sm:py-6">
        <section aria-label="Status summary" className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          <StatusCount label="LIVE" count={counts.LIVE} color="text-emerald-300" />
          <StatusCount label="STAGED" count={counts.STAGED} color="text-blue-300" />
          <StatusCount label="MODELED" count={counts.MODELED} color="text-amber-300" />
          <StatusCount label="EXTERNAL" count={counts.EXTERNAL} color="text-cyan-300" />
          <StatusCount label="SPEC" count={counts.SPECIFICATION} color="text-violet-300" />
          <StatusCount label="BLOCKED" count={counts.BLOCKED} color="text-red-300" />
          <StatusCount label="ARCHIVED" count={counts.ARCHIVED} color="text-ink-400" />
        </section>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {LAYER_DEFINITIONS.map((layer) => (
            <LayerPanel key={layer.id} layerId={layer.id} name={layer.name} subtitle={layer.subtitle} />
          ))}
        </div>
      </main>
    </>
  );
}

function StatusCount({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <div className="panel panel-pad text-center">
      <div className={`num text-2xl font-semibold ${color}`}>{count}</div>
      <div className="text-[11px] uppercase tracking-wider text-ink-400">{label}</div>
    </div>
  );
}

function LayerPanel({ layerId, name, subtitle }: { layerId: OperationalLayer; name: string; subtitle: string }) {
  const modules = getModulesByLayer(layerId);

  return (
    <Panel title={name} subtitle={subtitle}>
      <div className="divide-y divide-ink-700/50">
        {modules.map((mod) => (
          <div key={mod.id} className="flex items-center justify-between gap-3 py-2.5">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-ink-100 truncate">{mod.name}</span>
                <HealthPill health={mod.health} />
              </div>
              <p className="mt-0.5 text-[11px] text-ink-400 truncate">{mod.description}</p>
            </div>
            <DeploymentPill status={mod.status as DeploymentBadge} />
          </div>
        ))}
      </div>
    </Panel>
  );
}
