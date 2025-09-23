"use client";
import useSWR, { mutate } from "swr";
import { getJson, postJson, API_BASE } from "../lib/api";
import React, { useEffect, useState } from "react";
import { SystemAlerts } from "../components/alerts/SystemAlerts";
import { Skeleton, SkeletonText } from "../components/ui/Skeleton";
import { InlineError } from "../components/ui/InlineError";

function Badge({ ok, label }: { ok: boolean; label: string }){
  return (
    <span style={{
      display:'inline-block', padding:'4px 8px', borderRadius:8,
      background: ok? '#E6FFFA':'#FFF5F5', color: ok? '#0F766E':'#9B1C1C',
      fontSize:12, marginRight:8, marginBottom:8, border:'1px solid #ddd'
    }}>{label}: {ok? 'OK':'FAIL'}</span>
  );
}

function formatCurrency(n: number): string {
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(n || 0); } catch { return `$${(n||0).toFixed(2)}`; }
}

function getArAging(forecast: any): Array<{label: string; amount: number}> {
  if (!forecast) return [];
  // Support either object with known buckets or an array
  const buckets: Array<{label: string; amount: number}> = [];
  const obj = forecast.ar_aging || forecast.arAging || null;
  if (Array.isArray(obj)) {
    return obj.map((x:any) => ({ label: x.label || `${x.bucket || 'bucket'}`, amount: Number(x.amount || 0) }));
  }
  if (obj && typeof obj === 'object') {
    const order = ['current','30','60','90','120+'];
    for (const key of Object.keys(obj)) {
      const label = key;
      buckets.push({ label, amount: Number(obj[key] || 0) });
    }
    // Sort by our preferred order if possible
    buckets.sort((a,b) => (order.indexOf(a.label) === -1 ? 999 : order.indexOf(a.label)) - (order.indexOf(b.label) === -1 ? 999 : order.indexOf(b.label)));
    return buckets;
  }
  return [];
}

// Invoices filter state kept module-wide to avoid prop drilling
let invoiceStatusFilter: string | null = null;
function InvoiceFilters() {
  const [val, setVal] = useState<string>(invoiceStatusFilter || 'all');
  useEffect(() => { invoiceStatusFilter = val === 'all' ? null : val; }, [val]);
  return (
    <div className="flex items-center gap-2 text-sm">
      <label className="text-gray-600">Status</label>
      <select className="border rounded px-2 py-1" value={val} onChange={(e)=>setVal(e.target.value)}>
        <option value="all">All</option>
        <option value="open">Open</option>
        <option value="paid">Paid</option>
        <option value="void">Void</option>
        <option value="overdue">Overdue</option>
      </select>
    </div>
  );
}

function filterInvoices(items: any[]): any[] {
  if (!items || !items.length) return [];
  if (!invoiceStatusFilter) return items;
  return items.filter((i:any) => (i.status || '').toLowerCase() === invoiceStatusFilter);
}

export default function Overview(){
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const refresh = { refreshInterval: autoRefresh ? 30000 : 0 } as const;
  // Per-panel toggles
  const [profitRefresh, setProfitRefresh] = useState(true);
  const [aiRefresh, setAiRefresh] = useState(true);
  const [pendingRefresh, setPendingRefresh] = useState(true);
  const [errorsRefresh, setErrorsRefresh] = useState(true);
  const [invoiceRefresh, setInvoiceRefresh] = useState(true);

  const { data: healthSummary, error: healthSummaryErr } = useSWR<any>(`${API_BASE}/health/summary`, getJson, refresh);
  const { data: healthData, error: healthDataErr } = useSWR<any>(`${API_BASE}/health/data`, getJson, refresh);
  const { data: profitLog } = useSWR<any>(`${API_BASE}/profit/log?limit=5`, getJson, { refreshInterval: (autoRefresh && profitRefresh) ? 30000 : 0 });
  const { data: aiDecisions } = useSWR<any>(`${API_BASE}/ai/decisions?limit=5`, getJson, { refreshInterval: (autoRefresh && aiRefresh) ? 30000 : 0 });
  const { data: invoices } = useSWR<any>(`${API_BASE}/finance/invoices?limit=5`, getJson, { refreshInterval: (autoRefresh && invoiceRefresh) ? 30000 : 0 });
  const { data: financeForecast, error: forecastErr } = useSWR<any>(`${API_BASE}/finance/forecast`, getJson, refresh);
  const { data: pending, error: pendingErr } = useSWR<any>(`${API_BASE}/pricing/pending?limit=5`, getJson, { refreshInterval: (autoRefresh && pendingRefresh) ? 30000 : 0 });
  const { data: integrationsHealth, error: integrationsErr } = useSWR<any>(`${API_BASE}/health/integrations`, getJson, { refreshInterval: (autoRefresh && errorsRefresh) ? 30000 : 0 });
  const { data: approvedTop } = useSWR<any>(`${API_BASE}/pricing/approved?limit=5`, getJson, { refreshInterval: (autoRefresh && pendingRefresh) ? 30000 : 0 });
  const { data: demoStatus, mutate: mutateDemoStatus } = useSWR<any>(`${API_BASE}/demo/status`, getJson, refresh);
  const redisConfigured = !!healthData?.redis?.configured;

  const [limit, setLimit] = useState<number>(50);
  const [busy, setBusy] = useState(false);
  const [seedBusy, setSeedBusy] = useState(false);

  // Persist auto-refresh preference
  useEffect(() => {
    try {
      const stored = window.localStorage.getItem('mm_auto_refresh');
      if (stored !== null) setAutoRefresh(stored === 'true');
    } catch {}
  }, []);
  useEffect(() => {
    try { window.localStorage.setItem('mm_auto_refresh', String(autoRefresh)); } catch {}
  }, [autoRefresh]);

  async function runQuickSim(){
    try{ setBusy(true); await postJson(`/pricing/simulate`, { limit }); }
    finally { setBusy(false); }
  }

  async function seedDemo(){
    try { setSeedBusy(true); await postJson(`/demo/seed`, { limit: 25 }); await mutateDemoStatus(); }
    finally { setSeedBusy(false); }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Overview</h1>
        <div className="flex items-center gap-2">
          <button
            className={`px-3 py-2 text-sm rounded-md border ${autoRefresh? 'bg-emerald-50 border-emerald-200 text-emerald-700':'bg-white hover:bg-gray-50'}`}
            onClick={() => setAutoRefresh(v => !v)}
            title="Toggle auto-refresh (30s)"
          >
            {autoRefresh? 'Auto-refresh: ON':'Auto-refresh: OFF'}
          </button>
          <a className="px-3 py-2 text-sm rounded-md border bg-white hover:bg-gray-50" href="/command-center">Open Command Center</a>
          <a className="px-3 py-2 text-sm rounded-md border bg-white hover:bg-gray-50" href="/pricing">Open Pricing Lab</a>
        </div>

      {(healthSummaryErr || healthDataErr || forecastErr) && (
        <InlineError
          title="Some dashboard data is unavailable"
          message={String((healthSummaryErr as any)?.message || healthSummaryErr || (healthDataErr as any)?.message || healthDataErr || (forecastErr as any)?.message || forecastErr)}
          onRetry={() => {
            mutate(`${API_BASE}/health/summary`);
            mutate(`${API_BASE}/health/data`);
            mutate(`${API_BASE}/finance/forecast`);
          }}
        />
      )}
      </div>

      {/* Get Started banner (shows when demo data is empty) */}
      {((demoStatus?.products || 0) < 3) && (
        <div className="mm-card p-4 flex items-center justify-between">
          <div>
            <div className="text-lg font-semibold">Get started in seconds</div>
            <div className="text-sm text-gray-600">Seed demo data so the dashboard has products, prices, and finance metrics to show.</div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={seedDemo} disabled={seedBusy} className={`mm-btn ${seedBusy ? '' : 'primary'}`}>
              {seedBusy ? 'Seeding…' : 'Seed Demo Data'}
            </button>
            <a href="/onboarding" className="mm-btn">Open Onboarding</a>
          </div>
        </div>
      )}

      {/* Top Products & Revenue Sparkline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="mm-card p-4">
          <h2 className="text-lg font-semibold mb-2">Top Products (Approved)</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {approvedTop ? (
              (approvedTop?.approved || approvedTop?.items || []).slice(0,5).map((p:any)=> (
                <div key={p.product_id || p.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div className="text-sm max-w-[380px] truncate" title={p.title}>{p.title || p.sku}</div>
                  <div className="text-sm font-mono">${p.proposed_price?.toFixed?.(2) ?? p.proposed_price ?? p.price ?? '—'}</div>
                </div>
              ))
            ) : (
              <SkeletonText lines={5} />
            )}
            {approvedTop && (!(approvedTop?.approved || approvedTop?.items)?.length) && <div className="text-sm text-gray-500">No approved products.</div>}
          </div>
        </div>
        <div className="mm-card p-4">
          <h2 className="text-lg font-semibold mb-2">Revenue (MTD)</h2>
          {financeForecast ? renderSparkline(financeForecast) : <Skeleton className="h-20 w-full" />}
        </div>
      </div>

      {/* Alerts */}
      <div className="mm-card p-4">
        <SystemAlerts />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Tile title="Database" value={healthData?.db?.ok ? 'Healthy' : 'Issue'} subtitle={`${healthData?.db?.latency_ms ?? '—'} ms`} ok={healthData?.db?.ok} />
        <Tile title="Redis" value={redisConfigured ? (healthData?.redis?.ok ? 'Healthy' : 'Issue') : 'Disabled'} subtitle={`${healthData?.redis?.latency_ms ?? '—'} ms`} ok={redisConfigured ? healthData?.redis?.ok : undefined} />
        <Tile title="Integrations" value={`${Object.values(healthData?.integrations||{}).filter((x:any)=>x?.configured).length} configured`} subtitle={`${Object.keys(healthData?.integrations||{}).length} total`} ok />
        <Tile title="AI Decisions" value={`${(aiDecisions?.items||[]).length}`} subtitle="Recent" ok />
      </div>

      {/* Finance KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Kpi title="Revenue MTD" value={formatCurrency(financeForecast?.revenue_mtd ?? financeForecast?.revenue ?? 0)} />
        <Kpi title="Expenses MTD" value={formatCurrency(financeForecast?.expenses_mtd ?? financeForecast?.expenses ?? 0)} />
        <Kpi title="Profit MTD" value={formatCurrency((financeForecast?.profit_mtd ?? financeForecast?.profit) ?? ((financeForecast?.revenue_mtd ?? 0) - (financeForecast?.expenses_mtd ?? 0)))} trend={((financeForecast?.profit_mtd ?? 0) >= 0) ? 'up' : 'down'} />
        <Kpi title="A/R Total" value={formatCurrency(financeForecast?.ar_total ?? 0)} />
        <Kpi title="A/P Total" value={formatCurrency(financeForecast?.ap_total ?? 0)} />
        <Kpi title="Runway (days)" value={`${financeForecast?.runway_days ?? '—'}`} />
      </div>

      {/* A/R Aging Breakdown */}
      <div className="mm-card p-4">
        <h2 className="text-lg font-semibold mb-2">A/R Aging</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
          {getArAging(financeForecast).map((b) => (
            <div key={b.label} className="p-3 bg-gray-50 rounded border">
              <div className="text-xs text-gray-600">{b.label}</div>
              <div className="text-base font-semibold">{formatCurrency(b.amount)}</div>
            </div>
          ))}
          {getArAging(financeForecast).length === 0 && (
            <div className="text-sm text-gray-500">No aging data.</div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="mm-card p-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Latest Profit Events</h2>
            <button className="text-xs px-2 py-1 border rounded" onClick={()=>setProfitRefresh(v=>!v)}>{profitRefresh? 'Pause':'Resume'}</button>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {(profitLog?.items||[]).map((r:any)=> (
              <div key={r.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                <div className="text-sm"><span className="font-medium">{r.module}</span><span className="text-gray-600"> — {r.action}</span></div>
                <span className="text-xs text-gray-500">{formatTime(r.timestamp)}</span>
              </div>
            ))}
            {(!profitLog?.items || profitLog.items.length===0) && <div className="text-sm text-gray-500">No events yet.</div>}
          </div>
        </div>

        <div className="mm-card p-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">AI Decisions</h2>
            <button className="text-xs px-2 py-1 border rounded" onClick={()=>setAiRefresh(v=>!v)}>{aiRefresh? 'Pause':'Resume'}</button>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {(aiDecisions?.items||[]).map((d:any)=> (
              <div key={d.id} className="p-2 bg-gray-50 rounded">
                <div className="flex justify-between text-sm"><span className="font-medium">{d.decision}</span><span className="text-xs text-gray-500">{formatTime(d.timestamp)}</span></div>
                <div className="text-xs text-gray-600 line-clamp-2">{d.reasoning}</div>
              </div>
            ))}
            {(!aiDecisions?.items || aiDecisions.items.length===0) && <div className="text-sm text-gray-500">No decisions yet.</div>}
          </div>
        </div>
      </div>

      <div className="mm-card p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Quick Simulation</h2>
          <a href="/pricing" className="text-sm text-blue-600 hover:underline">Open full Pricing Lab →</a>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm">Limit</label>
          <input type="number" className="border rounded px-2 py-1 w-24" value={limit} onChange={e=>setLimit(parseInt(e.target.value||'0'))} />
          <button onClick={runQuickSim} disabled={busy} className={`mm-btn ${busy ? '' : 'primary'}`}>{busy? 'Running…':'Run Simulation'}</button>
        </div>
      </div>

      <div className="mm-card p-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">Recent Invoices</h2>
          <div className="flex items-center gap-2">
            <button className="text-xs px-2 py-1 border rounded" onClick={()=>setInvoiceRefresh(v=>!v)}>{invoiceRefresh? 'Pause':'Resume'}</button>
            <InvoiceFilters />
          </div>
        </div>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {filterInvoices(invoices?.items || []).map((inv: any) => (
            <div key={inv.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <div className="text-sm">
                <span className="font-medium">{inv.invoice_number || inv.id}</span>
                <span className="text-gray-600"> — {inv.status || 'open'}</span>
              </div>
              <div className="text-right text-sm">
                <div className="font-mono">${inv.amount_total?.toFixed?.(2) ?? inv.amount_total ?? '0.00'}</div>
                <div className="text-xs text-gray-500">{formatTime(inv.created_at || inv.issued_at || new Date().toISOString())}</div>
              </div>
            </div>
          ))}
          {filterInvoices(invoices?.items || []).length === 0 && (
            <div className="text-sm text-gray-500">No invoices.</div>
          )}
        </div>
      </div>
    </div>
  );
}

const th: React.CSSProperties = { textAlign:'left', padding:'8px', borderBottom:'1px solid #eee', background:'#fafafa' };
const td: React.CSSProperties = { padding:'8px', borderBottom:'1px solid #f2f2f2' };
const table: React.CSSProperties = { width: '100%', borderCollapse: 'collapse' };

function formatTime(timestamp?: string | Date): string {
  if (!timestamp) return '–';
  const d = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  return d.toLocaleTimeString();
}

function Tile({ title, value, subtitle, ok }: { title: string; value: React.ReactNode; subtitle?: string; ok?: boolean }){
  return (
    <div className="group relative">
      <div className={`absolute inset-0 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${ok===false? 'bg-red-500/20' : 'bg-blue-500/10'}`}></div>
      <div className="relative bg-white rounded-2xl p-5 border">
        <div className="text-sm text-gray-600">{title}</div>
        <div className="text-2xl font-bold mt-1">{value}</div>
        {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
      </div>
    </div>
  );
}

function Kpi({ title, value, trend }: { title: string; value: React.ReactNode; trend?: 'up'|'down'|'stable' }) {
  const color = trend === 'up' ? 'text-emerald-600' : trend === 'down' ? 'text-red-600' : 'text-gray-900';
  const icon = trend === 'up' ? '↗︎' : trend === 'down' ? '↘︎' : '→';
  return (
    <div className="bg-white rounded-xl p-4 border">
      <div className="flex items-center justify-between mb-1">
        <div className="text-sm text-gray-600">{title}</div>
        <div className={`text-xs ${trend==='up'?'text-emerald-600':trend==='down'?'text-red-600':'text-gray-400'}`}>{icon}</div>
      </div>
      <div className={`text-xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}

function getErrorItems(integrationsHealth: any): any[] {
  if (!integrationsHealth) return [];
  const items: any[] = [];
  // Object form: { key: { status, message, last_probe } }
  if (typeof integrationsHealth === 'object' && !Array.isArray(integrationsHealth)) {
    for (const k of Object.keys(integrationsHealth)) {
      const v: any = (integrationsHealth as any)[k];
      if (!v) continue;
      const status = (v.status || '').toString().toLowerCase();
      if (status.includes('error') || status.includes('fail') || v.message) {
        items.push({ key: k, ...v });
      }
    }
  }
  // Array form: [ { key/name, status, message } ]
  if (Array.isArray(integrationsHealth)) {
    for (const v of integrationsHealth) {
      const status = (v?.status || '').toString().toLowerCase();
      if (status.includes('error') || status.includes('fail') || v?.message) {
        items.push(v);
      }
    }
  }
  return items;
}

function labelFor(key: string): string {
  const map: Record<string,string> = {
    amazon_sp_api: 'Amazon SP-API', ebay: 'eBay', walmart: 'Walmart', cj: 'CJ', autods: 'AutoDS', keepa: 'Keepa', gtrends: 'Google Trends'
  };
  return map[key] || key;
}

function renderSparkline(forecast: any){
  const pts = (forecast?.revenue_series || forecast?.revenueSeries || []).map((v:any, i:number)=>({x:i, y:Number(v.amount||v)||0}));
  if (!pts.length) return <div className="text-sm text-gray-500">No revenue data.</div>;
  const w = 360, h = 80, p=6;
  const max = Math.max(...pts.map(p=>p.y)) || 1;
  const min = Math.min(...pts.map(p=>p.y)) || 0;
  const span = Math.max(max-min, 1);
  const scaleX = (i:number)=> p + i * ((w-2*p)/Math.max(pts.length-1,1));
  const scaleY = (y:number)=> h - p - ((y - min)/span) * (h-2*p);
  const d = pts.map((pt, i)=> `${i===0? 'M':'L'} ${scaleX(i)} ${scaleY(pt.y)}`).join(' ');
  return (
    <svg width={w} height={h} className="block">
      <path d={d} fill="none" stroke="#2563eb" strokeWidth="2" />
      {pts.map((pt,i)=> <circle key={i} cx={scaleX(i)} cy={scaleY(pt.y)} r={1.8} fill="#2563eb" />)}
    </svg>
  );
}
