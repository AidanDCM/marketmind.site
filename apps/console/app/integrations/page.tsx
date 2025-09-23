"use client";
import * as React from "react";
import useSWR, { mutate } from "swr";
import { API_BASE, authHeaders } from "../../lib/api";
import { InlineError } from "../../components/ui/InlineError";
import { Skeleton, SkeletonText } from "../../components/ui/Skeleton";
import { useToast } from "../../components/ui/Toast";

const fetcher = (url: string) => fetch(url, { headers: authHeaders(), cache: 'no-store' }).then(r => r.json());

export default function IntegrationsPage() {
  const { data: healthData, error: hdErr } = useSWR(`${API_BASE}/health/data`, fetcher, { refreshInterval: 30000 });
  const { data: integrationsHealth, error: ihErr } = useSWR(`${API_BASE}/health/integrations`, fetcher, { refreshInterval: 30000 });
  const { error: toastError, success } = useToast();

  const integrations = healthData?.integrations || {};
  const recent = integrationsHealth?.recent_calls || integrationsHealth?.calls || [];

  const loading = !healthData && !hdErr;
  const calls = integrationsHealth?.recent_calls || integrationsHealth?.calls || [];

  // Toast when errors occur and when they recover
  const hasError = Boolean(hdErr || ihErr);
  const prevHasError = React.useRef<boolean>(false);
  React.useEffect(() => {
    if (hasError && !prevHasError.current) {
      toastError("Unable to load integrations data");
    } else if (!hasError && prevHasError.current) {
      success("Integrations data recovered");
    }
    prevHasError.current = hasError;
  }, [hasError, toastError, success]);

  async function testIntegration(key: string){
    try {
      const fresh = await fetcher(`${API_BASE}/health/integrations`);
      const h = normalizeHealth(fresh, key);
      if (h && (h.status === 'healthy' || h.ok === true)) {
        const ms = h.latency_ms != null ? ` (${h.latency_ms} ms)` : '';
        success(`${labelFor(key)} healthy${ms}`);
      } else {
        const msg = h?.message || h?.error || 'Failed';
        toastError(`${labelFor(key)} error: ${msg}`);
      }
      // Revalidate cache
      mutate(`${API_BASE}/health/integrations`);
    } catch(e:any){
      toastError(`${labelFor(key)} test failed: ${e?.message||e}`);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Integrations</h1>
        <button className="mm-btn" onClick={() => {
          mutate(`${API_BASE}/health/data`);
          mutate(`${API_BASE}/health/integrations`);
          success("Refreshing integrations…");
        }}>Refresh</button>
      </div>

      {(hdErr || ihErr) && (
        <InlineError title="Unable to load integrations" message={String((hdErr as any)?.message || hdErr || ihErr)} onRetry={() => { mutate(`${API_BASE}/health/data`); mutate(`${API_BASE}/health/integrations`); }} />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="mm-card p-4"><SkeletonText lines={3} /></div>
          ))
        ) : (
          Object.keys(integrations).map((key) => (
            <IntegrationCard key={key} keyName={key} configured={!!integrations[key]?.configured} health={normalizeHealth(integrationsHealth, key)} onTest={()=>testIntegration(key)} />
          ))
        )}
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-3">Recent API Calls</h2>
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {!integrationsHealth && !ihErr ? (
            <SkeletonText lines={4} />
          ) : (
            calls.length ? calls.map((c: any, i: number) => (
              <div key={i} className="mm-card p-2 flex justify-between items-center">
                <div className="flex items-center gap-2 text-sm">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${c.status===200? 'bg-emerald-100 text-emerald-700':'bg-red-100 text-red-700'}`}>{c.status}</span>
                  <span className="font-medium">{c.platform || c.integration || 'API'}</span>
                  <span className="text-gray-600">{c.endpoint || c.path || ''}</span>
                </div>
                <span className="text-xs text-gray-500">{formatTime(c.timestamp || c.time || c.ts)}</span>
              </div>
            )) : (<div className="text-sm text-gray-500">No recent calls.</div>)
          )}
        </div>
      </section>
    </div>
  );
}

function IntegrationCard({ keyName, configured, health, onTest }: { keyName: string; configured: boolean; health?: any; onTest?: () => void }) {
  return (
    <div className="mm-card p-4">
      <div className="flex items-center justify-between">
        <div className="font-medium text-sm">{labelFor(keyName)}</div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${configured? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-gray-50 text-gray-700 border-gray-200'}`}>
            {configured? 'Configured' : 'Disabled'}
          </span>
          <button
            className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50 disabled:opacity-50"
            onClick={onTest}
            disabled={!configured || !onTest}
            aria-label={`Test ${labelFor(keyName)} health`}
          >
            Test
          </button>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-600">
        <div className="flex justify-between"><span>Status</span><span className="font-mono">{health?.status || (configured? 'active':'inactive')}</span></div>
        <div className="flex items-center justify-between">
          <span>Latency</span>
          {(() => {
            const lat = typeof health?.latency_ms === 'number' ? health.latency_ms as number : null;
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
        </div>
        <div className="flex justify-between"><span>Rate Limit</span><span className="font-mono">{health?.rate_limit || '—'}</span></div>
        <div className="flex justify-between"><span>Remaining</span><span className="font-mono">{health?.remaining ?? '—'}</span></div>
      </div>
      {health?.message && <div className="mt-2 text-xs text-gray-500">{health.message}</div>}
    </div>
  );
}

function labelFor(key: string): string {
  const map: Record<string,string> = {
    amazon_sp_api: 'Amazon SP-API', ebay: 'eBay', walmart: 'Walmart', cj: 'CJ', autods: 'AutoDS', keepa: 'Keepa', gtrends: 'Google Trends'
  };
  return map[key] || key;
}

function normalizeHealth(h: any, key: string) {
  if (!h) return undefined;
  const normKey = key;
  if (Array.isArray(h)) {
    return h.find((e) => (e.key || e.name)?.toLowerCase()?.includes(normKey.replace('_','')));
  }
  if (typeof h === 'object') {
    // Support shape from /health/integrations { checks: { [key]: { status, message, details } } }
    if (h.checks && h.checks[normKey]) {
      const chk = h.checks[normKey];
      const details = chk?.details || {};
      return { ...details, status: chk?.status ? 'healthy' : 'error', message: chk?.message };
    }
    return h[normKey];
  }
  return undefined;
}

function formatTime(ts?: string | Date) {
  if (!ts) return '—';
  const d = typeof ts === 'string'? new Date(ts) : ts;
  return d.toLocaleTimeString();
}
