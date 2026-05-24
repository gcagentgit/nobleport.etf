import React from 'react';
import type { Health, Severity } from '@/lib/dashboard/types';

const dotColor: Record<Health, string> = {
  healthy: 'bg-emerald-400',
  degraded: 'bg-yellow-400',
  unhealthy: 'bg-red-400',
  unknown: 'bg-ink-400',
};

const wrapper: Record<Health, string> = {
  healthy: 'pill-ok',
  degraded: 'pill-warn',
  unhealthy: 'pill-err',
  unknown: 'pill-mute',
};

export function HealthPill({ health, label }: { health: Health; label?: string }) {
  return (
    <span className={wrapper[health]}>
      <span className={`h-1.5 w-1.5 rounded-full ${dotColor[health]}`} />
      {label ?? health}
    </span>
  );
}

export function SeverityPill({ severity }: { severity: Severity }) {
  if (severity === 'critical') return <span className="pill-err">CRITICAL</span>;
  if (severity === 'warn') return <span className="pill-warn">WARN</span>;
  return <span className="pill-info">INFO</span>;
}

const statusClass: Record<string, string> = {
  ok: 'pill-ok',
  warn: 'pill-warn',
  err: 'pill-err',
  info: 'pill-info',
  muted: 'pill-mute',
};

export function StatusPill({ status, label }: { status: string; label: string }) {
  return <span className={statusClass[status] ?? 'pill-mute'}>{label}</span>;
}
