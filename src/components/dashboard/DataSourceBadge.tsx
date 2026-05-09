import type { DataSource } from '@/lib/dashboard/api';

const STYLES: Record<DataSource, { label: string; cls: string; hint: string }> = {
  live: {
    label: 'LIVE',
    cls: 'pill-ok',
    hint: 'Every field on this view came from a live service.',
  },
  mixed: {
    label: 'MIXED',
    cls: 'pill-warn',
    hint: 'Some fields are live; some are fixtures pending an upstream service.',
  },
  fixture: {
    label: 'FIXTURE',
    cls: 'pill-info',
    hint: 'No live source for this view yet. Showing deterministic fixtures.',
  },
  unknown: {
    label: 'UNKNOWN',
    cls: 'pill-mute',
    hint: 'Gateway did not return X-Data-Source.',
  },
};

export function DataSourceBadge({ source }: { source: DataSource }) {
  const s = STYLES[source];
  return (
    <span className={s.cls} title={s.hint}>
      {s.label}
    </span>
  );
}
