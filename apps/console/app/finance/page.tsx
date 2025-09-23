"use client";

import Link from "next/link";
import useSWR, { mutate } from "swr";
import { getJson, API_BASE } from "../../lib/api";
import { InlineError } from "../../components/ui/InlineError";
import { SkeletonText } from "../../components/ui/Skeleton";

export default function FinanceIndex(){
  const { data: invoices, error: invErr } = useSWR<any>(`${API_BASE}/finance/invoices?limit=5`, getJson);
  const { data: batches, error: batErr } = useSWR<any>(`${API_BASE}/finance/ledger/batches?limit=5`, getJson);
  const { data: entries, error: entErr } = useSWR<any>(`${API_BASE}/finance/ledger/entries?limit=5`, getJson);
  const { data: forecast, error: fErr } = useSWR<any>(`${API_BASE}/finance/forecast`, getJson);

  const invoiceCount = (invoices?.items||[]).length;
  const batchCount = (batches?.items||[]).length;
  const entryCount = (entries?.items||[]).length;
  const forecastCount = (forecast?.items||[]).length;
  const invLoading = !invoices && !invErr;
  const batLoading = !batches && !batErr;
  const entLoading = !entries && !entErr;
  const fLoading = !forecast && !fErr;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Finance</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card href="/finance/invoices" title="Invoices" subtitle="View and filter supplier invoices" stat={`${invoiceCount} recent`} icon="🧾" loading={invLoading} error={invErr} onRetry={()=>mutate(`${API_BASE}/finance/invoices?limit=5`)} />
        <Card href="/finance/ledger" title="Ledger" subtitle="Batches & entries with drilldown" stat={`${batchCount} batches / ${entryCount} entries`} icon="📚" loading={batLoading || entLoading} error={batErr || entErr} onRetry={()=>{ mutate(`${API_BASE}/finance/ledger/batches?limit=5`); mutate(`${API_BASE}/finance/ledger/entries?limit=5`); }} />
        <Card href="/finance/forecast" title="Forecast" subtitle="Cashflow trends & A/R aging" stat={`${forecastCount} periods`} icon="📈" loading={fLoading} error={fErr} onRetry={()=>mutate(`${API_BASE}/finance/forecast`)} />
        <Card href="/finance/recon" title="Reconciliation" subtitle="Start and monitor recon tasks" icon="🔄" />
      </div>

      <div className="text-sm text-gray-600">
        Need help? Open Onboarding for credentials and setup, or check Integrations for connection status.
      </div>
    </div>
  );
}

function Card({ href, title, subtitle, stat, icon, loading, error, onRetry }:{ href:string; title:string; subtitle:string; stat?:string; icon?:string; loading?: boolean; error?: any; onRetry?: ()=>void }){
  return (
    <Link href={href} className="group block bg-white rounded-xl border p-5 hover:shadow-sm transition">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm text-gray-600">{subtitle}</div>
          <div className="text-lg font-semibold">{title}</div>
          {error ? (
            <div className="mt-2"><InlineError title="Data unavailable" message={String((error as any)?.message || error)} onRetry={onRetry} /></div>
          ) : loading ? (
            <div className="mt-2"><SkeletonText lines={1} /></div>
          ) : (stat && <div className="text-xs text-gray-500 mt-1">{stat}</div>)}
        </div>
        <div className="text-2xl">{icon || "→"}</div>
      </div>
    </Link>
  );
}
