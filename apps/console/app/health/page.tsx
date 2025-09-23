"use client";
import * as React from "react";
import useSWR, { mutate } from "swr";
import { API_BASE, authHeaders } from "../../lib/api";
import { useToast } from "../../components/ui/Toast";
import { Th, Td } from "../../components/ui/Table";

const fetcher = (url: string) => fetch(url, { headers: authHeaders(), cache: 'no-store' }).then(r => r.json());

export default function HealthPage() {
  const { data: health, error: hErr } = useSWR(`${API_BASE}/health/data`, fetcher, { refreshInterval: 30000 });
  const { data: integ, error: ihErr } = useSWR(`${API_BASE}/health/integrations`, fetcher, { refreshInterval: 30000 });
  const { success, error: pushError } = useToast();
  const [statusFilter, setStatusFilter] = React.useState<'all'|'healthy'|'error'>("all");

  const dbOk = !!health?.db?.ok;
  const redisOk = !!health?.redis?.ok;
  const redisConfigured = !!health?.redis?.configured;
  const integrations = health?.integrations || {};

  // Build checks list from /health/integrations
  const checks = React.useMemo(() => {
    const entries = Object.entries((integ?.checks || {}) as Record<string, any>);
    const mapped = entries.map(([key, val]) => {
      const status = val?.status ? 'healthy' : 'error';
      const latency = val?.details?.latency_ms ?? null;
      const enabled = val?.details?.enabled;
      const message = val?.message as string | undefined;
      return { key, status, latency, enabled, message };
    });
    return mapped.filter(c => statusFilter === 'all' ? true : c.status === statusFilter);
  }, [integ, statusFilter]);

  // Toast on error/recovery
  const hasError = Boolean(hErr || ihErr);
  const prevHasError = React.useRef<boolean>(false);
  React.useEffect(() => {
    if (hasError && !prevHasError.current) {
      pushError("Health data unavailable");
    } else if (!hasError && prevHasError.current) {
      success("Health data recovered");
    }
    prevHasError.current = hasError;
  }, [hasError, pushError, success]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">System Health</h1>
        <button
          className="px-3 py-1.5 text-sm rounded-md border bg-white hover:bg-gray-50"
          onClick={() => { success("Rechecking health…"); mutate(`${API_BASE}/health/data`); mutate(`${API_BASE}/health/integrations`); }}
        >
          Recheck
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <HealthCard title="Database" status={dbOk? 'up':'down'} subtitle={`${health?.db?.latency_ms ?? '—'} ms`} />
        <HealthCard title="Redis" status={redisConfigured ? (redisOk? 'up':'down') : 'disabled'} subtitle={`${health?.redis?.latency_ms ?? '—'} ms`} />
        <HealthCard title="Integrations (Configured)" status="up" count={`${Object.values(integrations).filter((x: any)=>x?.configured).length} / ${Object.keys(integrations).length}`} />
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-3">Integrations</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.keys(integrations).map((k) => (
            <div key={k} className="border rounded-lg bg-white p-3 flex items-center justify-between">
              <div className="text-sm font-medium">{k}</div>
              <Badge ok={!!integrations[k]?.configured} />
            </div>
          ))}
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">Detailed Checks</h2>
          <div className="flex items-center gap-2 text-xs">
            <button className={`px-2 py-1 rounded border ${statusFilter==='all'?'bg-blue-50 border-blue-200':'bg-white'}`} onClick={()=>setStatusFilter('all')}>All</button>
            <button className={`px-2 py-1 rounded border ${statusFilter==='healthy'?'bg-emerald-50 border-emerald-200':'bg-white'}`} onClick={()=>setStatusFilter('healthy')}>Healthy</button>
            <button className={`px-2 py-1 rounded border ${statusFilter==='error'?'bg-red-50 border-red-200':'bg-white'}`} onClick={()=>setStatusFilter('error')}>Error</button>
          </div>
        </div>
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="w-full text-sm" aria-label="Integration health checks">
            <caption className="sr-only">Integration health checks with status and latency</caption>
            <thead>
              <tr className="bg-gray-50 text-left">
                <Th>Check</Th><Th>Status</Th><Th>Latency</Th><Th>Message</Th>
              </tr>
            </thead>
            <tbody>
              {!integ ? (
                <tr><Td colSpan={4}><span className="text-gray-500">Loading…</span></Td></tr>
              ) : (checks.length ? checks.map((c) => (
                <tr key={c.key} className="border-t">
                  <Td className="font-mono">{c.key}</Td>
                  <Td>{c.status === 'healthy' ? <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">healthy</span> : <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-200">error</span>}</Td>
                  <Td>
                    {(() => {
                      const lat = typeof c.latency === 'number' ? c.latency as number : null;
                      const text = lat != null ? `${lat} ms` : '—';
                      const color = lat == null ? 'text-gray-500' : lat < 100 ? 'text-emerald-600' : lat < 500 ? 'text-amber-600' : 'text-red-600';
                      const dot = lat == null ? 'bg-gray-400' : lat < 100 ? 'bg-emerald-500' : lat < 500 ? 'bg-amber-500' : 'bg-red-500';
                      return (
                        <span className={`inline-flex items-center gap-1 font-mono ${color}`}>
                          <span className={`inline-block w-2 h-2 rounded-full ${dot}`} aria-hidden="true" />
                          {text}
                        </span>
                      );
                    })()}
                  </Td>
                  <Td>{c.message || (c.enabled===false ? 'not configured' : '—')}</Td>
                </tr>
              )) : (
                <tr><Td colSpan={4}><span className="text-gray-500">No checks.</span></Td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function HealthCard({ title, status, subtitle, count }: { title: string; status?: 'up'|'down'|'disabled'; subtitle?: string; count?: string }) {
  return (
    <div className="group relative">
      <div className={`absolute inset-0 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${status==='up' ? 'bg-emerald-500/20' : status==='down' ? 'bg-red-500/20' : 'bg-gray-500/10'}`}></div>
      <div className="relative bg-white rounded-2xl p-5 border">
        <div className="text-sm text-gray-600">{title}</div>
        <div className="mt-2 flex items-baseline gap-2">
          {typeof count === 'string' ? (
            <span className="text-2xl font-bold">{count}</span>
          ) : (
            <span className={`text-2xl font-bold ${status==='up' ? 'text-emerald-600' : status==='down' ? 'text-red-600' : 'text-gray-600'}`}>
              {status==='up' ? 'Healthy' : status==='down' ? 'Issue' : 'Disabled'}
            </span>
          )}
          {subtitle && <span className="text-xs text-gray-500">{subtitle}</span>}
        </div>
      </div>
    </div>
  );
}

function Badge({ ok }: { ok: boolean }) {
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${ok ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
      {ok ? 'Configured' : 'Missing'}
    </span>
  );
}


