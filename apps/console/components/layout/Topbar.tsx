"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { clearToken, API_BASE, getJson, postJson } from "../../lib/api";
import { useRole } from "../../lib/auth";
import { useToast } from "../ui/Toast";

export default function Topbar() {
  const [token, setToken] = useState<string | null>(null);
  const AUTH_DISABLED = (process.env.NEXT_PUBLIC_AUTH_DISABLED || "false").toLowerCase() === "true";
  const { role, tokenPresent } = useRole();
  const [brandName, setBrandName] = useState<string>("MarketMind");
  const [brandLogo, setBrandLogo] = useState<string>("");
  const envName = (process.env.NEXT_PUBLIC_APP_ENV || process.env.NODE_ENV || "dev").toString();
  const { data: health } = useSWR<any>(`${API_BASE}/health/summary`, getJson, { refreshInterval: 60000 });
  const healthOk = !!health?.db?.ok && (!!health?.redis?.configured ? !!health?.redis?.ok : true);
  const { data: orc, mutate: mutateOrc } = useSWR<any>(`${API_BASE}/orchestrator/health`, getJson, { refreshInterval: 60000 });
  const pricingFrozen = !!orc?.frozen?.pricing;
  const toast = useToast();
  useEffect(() => {
    try { setToken(typeof window !== 'undefined' ? window.localStorage.getItem('api_token') : null); } catch {}
    const handler = () => {
      try { setToken(typeof window !== 'undefined' ? window.localStorage.getItem('api_token') : null); } catch {}
    };
    window.addEventListener('storage', handler);
    // Load branding
    try {
      const b = typeof window !== 'undefined' ? window.localStorage.getItem('mm_brand_name') : '';
      const l = typeof window !== 'undefined' ? window.localStorage.getItem('mm_brand_logo') : '';
      if (b) setBrandName(b);
      if (l) setBrandLogo(l);
    } catch {}
    return () => window.removeEventListener('storage', handler);
  }, []);

  return (
    <header className="h-14 bg-white/80 backdrop-blur border-b border-gray-200 flex items-center justify-between px-4">
      <div className="flex items-center gap-3 min-w-0">
        <div className="hidden md:flex items-center gap-2 min-w-0">
          {brandLogo ? (
            <img src={brandLogo} alt={brandName} className="w-5 h-5 rounded object-cover" />
          ) : (
            <span>🧠</span>
          )}
          <span className="text-sm text-gray-800 font-medium truncate" title={brandName}>{brandName}</span>
          <span className="text-gray-400">/</span>
          <span className="text-sm text-gray-600">Dashboard</span>
        </div>
        <span className={`hidden sm:inline-flex items-center gap-1 text-[11px] px-2 py-0.5 border rounded-md ${healthOk? 'bg-emerald-50 text-emerald-700 border-emerald-200':'bg-yellow-50 text-yellow-700 border-yellow-200'}`} title="Core system health">
          <span className={`inline-block w-2 h-2 rounded-full ${healthOk? 'bg-emerald-500':'bg-yellow-500'}`} />
          {healthOk? 'Healthy':'Degraded'}
        </span>
        {AUTH_DISABLED && (
          <span className="text-[11px] px-2 py-0.5 border rounded-md bg-amber-50 text-amber-700">Local Mode</span>
        )}
        {!AUTH_DISABLED && tokenPresent && (
          <span className="text-[11px] px-2 py-0.5 border rounded-md bg-blue-50 text-blue-700">
            Role: {role || 'unknown'}
          </span>
        )}
        <span className="hidden md:inline text-[11px] px-2 py-0.5 border rounded-md bg-gray-50 text-gray-700" title="Environment">
          {envName}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" onClick={() => location.reload()} title="Refresh">↻ Refresh</button>
        <button
          className={`px-2 py-1 text-xs rounded-md border ${pricingFrozen ? 'bg-amber-50 hover:bg-amber-100 text-amber-800' : 'bg-white hover:bg-gray-50'}`}
          onClick={async () => {
            try {
              await postJson(`/orchestrator/freeze/pricing?freeze=${(!pricingFrozen).toString()}`);
              await mutateOrc();
              toast.success(pricingFrozen ? 'Resumed pricing' : 'Paused pricing');
            } catch (e:any) {
              toast.error(e?.message || 'Failed to toggle pricing');
            }
          }}
          title={pricingFrozen ? 'Resume Pricing' : 'Pause Pricing'}
        >
          {pricingFrozen ? 'Resume Pricing' : 'Pause Pricing'}
        </button>
        <Link className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" href="/onboarding">Onboarding</Link>
        {!AUTH_DISABLED && token ? (
          <button
            className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50"
            onClick={() => { clearToken(); setToken(null); }}
            title="Logout"
          >Logout</button>
        ) : !AUTH_DISABLED ? (
          <Link className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" href="/login">Login</Link>
        ) : null}
      </div>
    </header>
  );
}
