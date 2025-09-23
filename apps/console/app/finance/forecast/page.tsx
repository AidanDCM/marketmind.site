"use client";

import useSWR, { mutate } from "swr";
import { getJson, API_BASE } from "../../../lib/api";
import { downloadCsv } from "../../../lib/csv";
import { InlineError } from "../../../components/ui/InlineError";
import { SkeletonText } from "../../../components/ui/Skeleton";
import { useToast } from "../../../components/ui/Toast";
import { Th, Td } from "../../../components/ui/Table";

export default function ForecastPage(){
  const { data, error } = useSWR<any>(`${API_BASE}/finance/forecast`, getJson, { refreshInterval: 30000 });
  const { success, error: pushError } = useToast();
  const items = (data?.items || []) as any[];
  const loading = !data && !error;

  // Toasts for error/recovery
  const hasError = Boolean(error);
  const prevHasError = (globalThis as any).__mm_forecast_prevErr ?? { current: false };
  if ((globalThis as any).__mm_forecast_prevErr === undefined) {
    (globalThis as any).__mm_forecast_prevErr = prevHasError;
  }
  if (hasError && !prevHasError.current) {
    pushError("Forecast data unavailable");
    prevHasError.current = true;
  } else if (!hasError && prevHasError.current) {
    success("Forecast data recovered");
    prevHasError.current = false;
  }

  const netSeries = items.map((i:any, idx:number)=> ({ x: idx, y: Number(i.net||0) }));
  const sum = (arr:number[]) => arr.reduce((a,b)=>a+b,0);
  const revenue = sum(items.map((i:any)=> Number(i.inflow||0)));
  const outflow = sum(items.map((i:any)=> Number(i.outflow||0)));
  const net = revenue - outflow;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Cashflow Forecast</h1>
        <div className="flex items-center gap-2">
          <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" onClick={()=>{ success('Refreshing forecast…'); mutate(`${API_BASE}/finance/forecast`); }}>Refresh</button>
          <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" onClick={()=> downloadCsv('forecast', ["period_start","period_end","inflow","outflow","net"], items.map(i => [i.period_start, i.period_end, i.inflow, i.outflow, i.net]))}>Export CSV</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {loading ? (
          <>
            <div className="bg-white rounded-xl border p-4"><SkeletonText lines={2} /></div>
            <div className="bg-white rounded-xl border p-4"><SkeletonText lines={2} /></div>
            <div className="bg-white rounded-xl border p-4"><SkeletonText lines={2} /></div>
          </>
        ) : (
          <>
            <Kpi title="Inflow (sum)" value={`$${revenue.toFixed(2)}`} />
            <Kpi title="Outflow (sum)" value={`$${outflow.toFixed(2)}`} />
            <Kpi title="Net (sum)" value={`$${net.toFixed(2)}`} trend={net>=0? 'up':'down'} />
          </>
        )}
      </div>

      <div className="bg-white rounded-xl border p-4">
        <h2 className="text-lg font-semibold mb-2">Net by Period</h2>
        {error && <InlineError message={String((error as any)?.message || error)} />}
        {loading ? <SkeletonText lines={4} /> : (netSeries.length ? <Sparkline points={netSeries} /> : <div className="text-sm text-gray-500">No forecast data.</div>)}
      </div>

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm" aria-label="Cashflow forecast table">
          <caption className="sr-only">Cashflow forecast with inflow, outflow, and net per period</caption>
          <thead>
            <tr className="bg-gray-50 text-left">
              <Th>Period Start</Th><Th>Period End</Th><Th>Inflow</Th><Th>Outflow</Th><Th>Net</Th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><Td colSpan={5}><SkeletonText lines={3} /></Td></tr>
            ) : (
              items.map((i:any, idx:number)=> (
                <tr key={idx} className="border-t">
                  <Td>{i.period_start}</Td><Td>{i.period_end}</Td><Td>${Number(i.inflow||0).toFixed(2)}</Td><Td>${Number(i.outflow||0).toFixed(2)}</Td><Td>${Number(i.net||0).toFixed(2)}</Td>
                </tr>
              ))
            )}
            {!loading && !items.length && <tr><Td colSpan={5}><div className="text-gray-500">No rows.</div></Td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Kpi({ title, value, trend }:{ title:string; value:string; trend?:'up'|'down'|'stable' }){
  const color = trend==='up'? 'text-emerald-600' : trend==='down'? 'text-red-600' : 'text-gray-900';
  return (
    <div className="bg-white rounded-xl border p-4">
      <div className="text-sm text-gray-600">{title}</div>
      <div className={`text-xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}

function Sparkline({ points }:{ points: Array<{x:number;y:number}> }){
  const w=560, h=120, p=8;
  const max = Math.max(...points.map(p=>p.y), 1);
  const min = Math.min(...points.map(p=>p.y), 0);
  const span = Math.max(max-min, 1e-6);
  const sx = (i:number)=> p + i * ((w-2*p)/Math.max(points.length-1,1));
  const sy = (y:number)=> h - p - ((y - min)/span) * (h-2*p);
  const d = points.map((pt,i)=>`${i===0?'M':'L'} ${sx(i)} ${sy(pt.y)}`).join(' ');
  return (
    <svg width={w} height={h} className="block">
      <path d={d} fill="none" stroke="#2563eb" strokeWidth="2" />
      {points.map((pt,i)=> <circle key={i} cx={sx(i)} cy={sy(pt.y)} r={1.8} fill="#2563eb" />)}
    </svg>
  );
}


