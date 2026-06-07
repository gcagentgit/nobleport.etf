'use client';

import { useEffect, useRef, useState } from 'react';

/**
 * KUZO Pro Terminal — chain ops view.
 *
 * Data provenance is explicit:
 *   LIVE   — Arbitrum block / gas / latency / balances, fetched directly from
 *            the public RPC in the BROWSER (no key; not subject to the backend's
 *            network allowlist). Real values for end users.
 *   LOCAL  — the SHA-256 treasury snapshot, from the backend's tamper-evident
 *            audit chain (/api/terminal/overview).
 *   NO FEED— websocket throughput and the trade tape have no real source wired,
 *            so they render as empty/unavailable rather than simulated.
 *
 * Nothing here is randomized. If a source is unreachable or unconfigured, the
 * panel says so.
 */

const C = {
  bg: '#0d0f12',
  surface: '#13161b',
  border: '#1e2330',
  muted: '#3a4055',
  dim: '#6b7594',
  text: '#c8d0e7',
  bright: '#e8edf8',
  green: '#22c55e',
  amber: '#f59e0b',
  red: '#ef4444',
  blue: '#3b82f6',
  purple: '#a78bfa',
  teal: '#2dd4bf',
  mono: "'JetBrains Mono', 'Fira Mono', 'Courier New', monospace",
};

type BadgeStatus =
  | 'LIVE'
  | 'UP'
  | 'DEGRADED'
  | 'DOWN'
  | 'ANCHORED'
  | 'PENDING'
  | 'UNCONFIGURED'
  | 'NO FEED'
  | 'STAGED';

interface TokenConfig {
  symbol: string;
  address: string;
  decimals: number;
}
interface ChainConfig {
  rpcUrl: string;
  chainId: number;
  wallet: string | null;
  tokens: TokenConfig[];
}
interface Snapshot {
  available: boolean;
  intact: boolean;
  detail: string;
  seq: number;
  hash: string | null;
  ts: string | null;
  status: 'ANCHORED' | 'PENDING' | 'DOWN';
}
interface ServiceRowData {
  name: string;
  status: string;
  detail: string;
}
interface Overview {
  generatedAt: string;
  deploymentStatus: string;
  snapshot: Snapshot;
  chain: ChainConfig;
  services: ServiceRowData[];
  feeds: { websocket: { available: boolean; note: string }; trades: { available: boolean; note: string } };
}

interface ChainLive {
  available: boolean;
  error?: string;
  block?: number;
  gasGwei?: number;
  latencyMs?: number;
  ethBalance?: number;
  balances: Record<string, number>;
}

const API_BASE = process.env.NEXT_PUBLIC_DASHBOARD_API_BASE ?? '';

function Badge({ status }: { status: BadgeStatus }) {
  const map: Record<string, { bg: string; color: string }> = {
    LIVE: { bg: '#14301e', color: C.green },
    UP: { bg: '#14301e', color: C.green },
    ANCHORED: { bg: '#0e1e38', color: C.blue },
    DEGRADED: { bg: '#2e2010', color: C.amber },
    PENDING: { bg: '#2e2010', color: C.amber },
    STAGED: { bg: '#2e2010', color: C.amber },
    DOWN: { bg: '#2a1010', color: C.red },
    UNCONFIGURED: { bg: '#181b22', color: C.dim },
    'NO FEED': { bg: '#181b22', color: C.dim },
  };
  const s = map[status] ?? map.UP;
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        background: s.bg,
        color: s.color,
        fontSize: 11,
        fontFamily: C.mono,
        padding: '2px 8px',
        borderRadius: 4,
        border: `1px solid ${s.color}22`,
      }}
    >
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: s.color, display: 'inline-block' }} />
      {status}
    </span>
  );
}

function Panel({ title, source, children }: { title: string; source?: string; children: React.ReactNode }) {
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: '14px 16px', minWidth: 0 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: 11, fontFamily: C.mono, color: C.dim, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{title}</span>
        {source && <span style={{ fontSize: 9, fontFamily: C.mono, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{source}</span>}
      </div>
      {children}
    </div>
  );
}

function Metric({ label, value, color, sub }: { label: string; value: string; color?: string; sub?: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <span style={{ fontSize: 11, color: C.dim, fontFamily: C.mono }}>{label}</span>
      <span style={{ fontSize: 20, fontWeight: 500, color: color || C.bright, fontFamily: C.mono }}>{value}</span>
      {sub && <span style={{ fontSize: 11, color: C.dim, fontFamily: C.mono }}>{sub}</span>}
    </div>
  );
}

async function rpc(rpcUrl: string, method: string, params: unknown[] = []): Promise<string> {
  const res = await fetch(rpcUrl, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }),
  });
  if (!res.ok) throw new Error(`rpc ${method} → ${res.status}`);
  const json = await res.json();
  if (json.error) throw new Error(`rpc ${method}: ${json.error.message ?? 'error'}`);
  return json.result as string;
}

function hexToNum(hex: string): number {
  return parseInt(hex, 16);
}
function unitsFromWei(hex: string, decimals: number): number {
  if (!hex || hex === '0x') return 0;
  return Number(BigInt(hex)) / 10 ** decimals;
}
function balanceOfData(wallet: string): string {
  return '0x70a08231' + wallet.toLowerCase().replace(/^0x/, '').padStart(64, '0');
}

const SHORT = (a?: string | null) => (a ? `${a.slice(0, 6)}…${a.slice(-4)}` : '—');

export function KuzoTerminal() {
  const [mounted, setMounted] = useState(false);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [overviewError, setOverviewError] = useState<string | null>(null);
  const [chain, setChain] = useState<ChainLive>({ available: false, balances: {} });
  const [lastChainAt, setLastChainAt] = useState<Date | null>(null);
  const chainCfgRef = useRef<ChainConfig | null>(null);

  // Backend overview (snapshot + service health). Local data — no outbound.
  useEffect(() => {
    setMounted(true);
    let alive = true;
    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/terminal/overview`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`overview → ${res.status}`);
        const data = (await res.json()) as Overview;
        if (!alive) return;
        setOverview(data);
        setOverviewError(null);
        chainCfgRef.current = data.chain;
      } catch (e) {
        if (alive) setOverviewError(e instanceof Error ? e.message : 'unreachable');
      }
    };
    load();
    const id = setInterval(load, 20000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  // Live Arbitrum data — fetched in the browser from the public RPC.
  useEffect(() => {
    const cfg = overview?.chain;
    if (!cfg?.rpcUrl) return;
    let alive = true;
    const refresh = async () => {
      try {
        const t0 = performance.now();
        const blockHex = await rpc(cfg.rpcUrl, 'eth_blockNumber');
        const latencyMs = Math.round(performance.now() - t0);
        const gasHex = await rpc(cfg.rpcUrl, 'eth_gasPrice');
        const next: ChainLive = {
          available: true,
          block: hexToNum(blockHex),
          gasGwei: unitsFromWei(gasHex, 9),
          latencyMs,
          balances: {},
        };
        if (cfg.wallet) {
          const ethHex = await rpc(cfg.rpcUrl, 'eth_getBalance', [cfg.wallet, 'latest']);
          next.ethBalance = unitsFromWei(ethHex, 18);
          for (const t of cfg.tokens) {
            const hex = await rpc(cfg.rpcUrl, 'eth_call', [{ to: t.address, data: balanceOfData(cfg.wallet) }, 'latest']);
            next.balances[t.symbol] = unitsFromWei(hex, t.decimals);
          }
        }
        if (!alive) return;
        setChain(next);
        setLastChainAt(new Date());
      } catch (e) {
        if (alive) setChain({ available: false, error: e instanceof Error ? e.message : 'rpc error', balances: {} });
      }
    };
    refresh();
    const id = setInterval(refresh, 12000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [overview?.chain?.rpcUrl, overview?.chain?.wallet]);

  const cfg = overview?.chain;
  const snap = overview?.snapshot;
  const tline = (d?: Date | string | null) => {
    if (!d || !mounted) return '—';
    const date = typeof d === 'string' ? new Date(d) : d;
    return date.toLocaleTimeString('en-US', { hour12: false });
  };
  const gasColor = chain.gasGwei == null ? C.dim : chain.gasGwei < 0.3 ? C.green : chain.gasGwei < 1 ? C.amber : C.red;

  return (
    <div style={{ fontFamily: C.mono, color: C.text }}>
      {/* Provenance banner */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 10,
          alignItems: 'center',
          justifyContent: 'space-between',
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderRadius: 8,
          padding: '10px 14px',
          marginBottom: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 26, height: 26, background: C.purple, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 13 }}>K</div>
          <div>
            <div style={{ fontSize: 14, color: C.bright, fontWeight: 500 }}>KUZO Pro Terminal</div>
            <div style={{ fontSize: 11, color: C.dim }}>
              Arbitrum One · chainId {cfg?.chainId ?? '—'} · refresh 12s
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 10, color: C.muted }}>
            LIVE = chain (browser RPC) · LOCAL = snapshot · NO FEED = not wired
          </span>
          <Badge status={(overview?.deploymentStatus as BadgeStatus) || 'STAGED'} />
        </div>
      </div>

      {overviewError && (
        <div style={{ fontSize: 11, color: C.amber, marginBottom: 10 }}>
          backend overview unreachable ({overviewError}) — set NEXT_PUBLIC_DASHBOARD_API_BASE. Live chain data below is independent.
        </div>
      )}

      {/* Top metrics — real chain values */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 10 }}>
        {[
          { label: 'block height', value: chain.block?.toLocaleString() ?? '—', color: C.text },
          { label: 'gas price', value: chain.gasGwei != null ? `${chain.gasGwei.toFixed(4)} gwei` : '—', color: gasColor },
          { label: 'rpc latency', value: chain.latencyMs != null ? `${chain.latencyMs}ms` : '—', color: chain.latencyMs != null && chain.latencyMs < 400 ? C.green : C.amber },
          { label: 'chain', value: chain.available ? 'LIVE' : 'UNREACHABLE', color: chain.available ? C.green : C.red },
        ].map((m) => (
          <div key={m.label} style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: '10px 14px' }}>
            <div style={{ fontSize: 10, color: C.dim, marginBottom: 4 }}>{m.label}</div>
            <div style={{ fontSize: 18, fontWeight: 500, color: m.color }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Network + Treasury snapshot */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
        <Panel title="Arbitrum One network" source="live · browser rpc">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Metric label="block" value={chain.block?.toLocaleString() ?? '—'} color={C.blue} />
            <Metric label="rpc latency" value={chain.latencyMs != null ? `${chain.latencyMs}ms` : '—'} color={C.teal} />
            <Metric
              label="wallet (ETH)"
              value={cfg?.wallet ? (chain.ethBalance != null ? chain.ethBalance.toFixed(4) : '…') : 'unconfigured'}
              color={cfg?.wallet ? C.teal : C.dim}
              sub={SHORT(cfg?.wallet)}
            />
            <Metric label="gas" value={chain.gasGwei != null ? `${chain.gasGwei.toFixed(4)} gwei` : '—'} color={gasColor} />
          </div>
          {chain.error && <div style={{ fontSize: 11, color: C.red, marginTop: 10 }}>{chain.error}</div>}
        </Panel>

        <Panel title="treasury snapshot" source="local · sha-256 chain">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
            {cfg?.wallet ? (
              cfg.tokens.map((t) => (
                <Metric
                  key={t.symbol}
                  label={`${t.symbol} balance`}
                  value={chain.balances[t.symbol] != null ? chain.balances[t.symbol].toLocaleString(undefined, { maximumFractionDigits: 2 }) : '…'}
                  color={t.symbol === 'USDC' ? C.green : C.purple}
                />
              ))
            ) : (
              <span style={{ fontSize: 12, color: C.dim }}>treasury wallet not configured</span>
            )}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: `1px solid ${C.border}`, paddingTop: 10 }}>
            <div>
              <div style={{ fontSize: 11, color: C.dim }}>SHA-256 anchor {snap?.hash ? `· ${snap.hash.slice(0, 10)}` : ''}</div>
              <div style={{ fontSize: 12, color: C.teal, marginTop: 2 }}>
                seq {snap?.seq ?? 0} · {tline(snap?.ts)} · {snap?.detail ?? '—'}
              </div>
            </div>
            <Badge status={(snap?.status as BadgeStatus) ?? 'PENDING'} />
          </div>
        </Panel>
      </div>

      {/* Services + Feeds */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Panel title="system services" source="local · config health">
          {(overview?.services ?? []).map((s) => (
            <div key={s.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 0', borderBottom: `1px solid ${C.border}` }}>
              <div>
                <div style={{ fontSize: 13, color: C.text }}>{s.name}</div>
                <div style={{ fontSize: 11, color: C.dim }}>{s.detail}</div>
              </div>
              <Badge status={s.status as BadgeStatus} />
            </div>
          ))}
          {!overview && !overviewError && <div style={{ fontSize: 12, color: C.dim }}>loading…</div>}
        </Panel>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Panel title="websocket / throughput" source="no feed">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 12, color: C.dim }}>{overview?.feeds.websocket.note ?? 'no live telemetry source wired'}</span>
              <Badge status="NO FEED" />
            </div>
          </Panel>
          <Panel title="trading activity feed" source="no feed">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 12, color: C.dim }}>{overview?.feeds.trades.note ?? 'no execution feed wired'}</span>
              <Badge status="NO FEED" />
            </div>
          </Panel>
          <Panel title="last refresh" source="client clock">
            <div style={{ fontSize: 12, color: C.teal }}>chain: {tline(lastChainAt)} · overview: {tline(overview?.generatedAt)}</div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
