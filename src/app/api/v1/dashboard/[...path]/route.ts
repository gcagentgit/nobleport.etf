/**
 * Catch-all proxy.
 *
 * Forwards GET requests at /api/v1/dashboard/* to the FastAPI gateway,
 * preserving the X-Data-Source header so external clients hitting the Next.js
 * origin see the same honest data-source signal the dashboard pages render.
 */

import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const DEFAULT_BASE = 'http://localhost:8000/api/v1/dashboard';

function gatewayBase(): string {
  return process.env.DASHBOARD_API_BASE ?? DEFAULT_BASE;
}

export async function GET(
  request: NextRequest,
  { params }: { params: { path?: string[] } },
) {
  const tail = (params.path ?? []).join('/');
  const search = request.nextUrl.search ?? '';
  const upstream = `${gatewayBase()}/${tail}${search}`;

  const token = process.env.DASHBOARD_API_TOKEN;
  let res: Response;
  try {
    res = await fetch(upstream, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      cache: 'no-store',
      signal: AbortSignal.timeout(5_000),
    });
  } catch (err) {
    const reason = err instanceof Error ? err.message : 'unknown';
    return NextResponse.json(
      { error: 'gateway_unreachable', detail: reason, upstream },
      { status: 502 },
    );
  }

  const body = await res.text();
  const out = new NextResponse(body, { status: res.status });
  const ct = res.headers.get('content-type');
  if (ct) out.headers.set('content-type', ct);
  const src = res.headers.get('x-data-source');
  if (src) out.headers.set('x-data-source', src);
  return out;
}
