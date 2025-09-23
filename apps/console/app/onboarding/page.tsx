"use client";

import React, { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { getJson, postJson } from "../../lib/api";
import { useToast } from "../../components/ui/Toast";

export default function OnboardingPage() {
  const { data: status, mutate } = useSWR<any>('/demo/status', getJson);
  const { data: health } = useSWR<any>('/health/data', getJson);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [step, setStep] = useState<number>(1); // 1:Health 2:Seed 3:Connect 4:Simulate 5:Brand 6:Finish
  const [simBusy, setSimBusy] = useState(false);
  const [simMsg, setSimMsg] = useState<string | null>(null);
  const [brandName, setBrandName] = useState<string>("");
  const [logoUrl, setLogoUrl] = useState<string>("");
  const [brandSaved, setBrandSaved] = useState<string | null>(null);
  const seeded = useMemo(() => (status?.products || 0) >= 3, [status]);
  const toast = useToast();
  // Load branding from local storage
  useEffect(() => {
    try {
      const b = typeof window !== 'undefined' ? window.localStorage.getItem('mm_brand_name') : '';
      const l = typeof window !== 'undefined' ? window.localStorage.getItem('mm_brand_logo') : '';
      if (b) setBrandName(b);
      if (l) setLogoUrl(l);
    } catch {}
  }, []);

  // Optional: auto-seed for local client teams
  const AUTO_SEED = (process.env.NEXT_PUBLIC_AUTO_SEED || "false").toLowerCase() === "true";
  const [autoSeeded, setAutoSeeded] = useState(false);
  useEffect(() => {
    if (!AUTO_SEED) return;
    if (autoSeeded) return;
    if (status === undefined) return; // wait for status load
    if (!seeded && !busy) {
      setAutoSeeded(true);
      // fire and forget
      seed(25).catch(()=>{});
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [AUTO_SEED, status, seeded, busy]);

  async function seed(limit = 25) {
    setMsg(null);
    setBusy(true);
    try {
      const res = await postJson<any>('/demo/seed', { limit });
      setMsg(res?.status === 'seeded' ? 'Demo data seeded successfully.' : 'Seeded (or already present).');
      toast.success('Demo data seeded');
      await mutate();
    } catch (e: any) {
      setMsg(e?.message || 'Failed to seed demo data');
      toast.error(e?.message || 'Failed to seed demo data');
    } finally {
      setBusy(false);
    }
  }
  async function runSim(limit = 25) {
    setSimMsg(null);
    setSimBusy(true);
    try {
      const res = await postJson<any>('/pricing/simulate', { limit });
      setSimMsg(res?.status || 'Simulation requested. Check Pricing for results.');
      toast.success('Simulation requested');
    } catch (e: any) {
      setSimMsg(e?.message || 'Failed to start simulation');
      toast.error(e?.message || 'Failed to start simulation');
    } finally {
      setSimBusy(false);
    }


  }

  function saveBranding(){
    try {
      if (typeof window !== 'undefined') {
        window.localStorage.setItem('mm_brand_name', brandName || '');
        window.localStorage.setItem('mm_brand_logo', logoUrl || '');
      }
      setBrandSaved('Branding saved. You may need to refresh to see changes in the sidebar.');
      toast.success('Branding saved');
    } catch (e:any) {
      setBrandSaved(e?.message || 'Failed to save branding');
      toast.error(e?.message || 'Failed to save branding');
    }
  }

  const nextDisabled = (step === 1 && !(health?.db?.ok)) || (step === 2 && !seeded);
  return (
    <div className="space-y-6">
      <div className="mm-card p-4 flex items-center gap-2 text-sm">
        <span className={`px-2 py-1 rounded-md border ${step===1? 'bg-blue-50 border-blue-200 text-blue-700':'bg-white'}`}>1. Health</span>
        <span className={`px-2 py-1 rounded-md border ${step===2? 'bg-blue-50 border-blue-200 text-blue-700':'bg-white'}`}>2. Seed</span>
        <span className={`px-2 py-1 rounded-md border ${step===3? 'bg-blue-50 border-blue-200 text-blue-700':'bg-white'}`}>3. Connect</span>
        <span className={`px-2 py-1 rounded-md border ${step===4? 'bg-blue-50 border-blue-200 text-blue-700':'bg-white'}`}>4. Simulate</span>
        <span className={`px-2 py-1 rounded-md border ${step===5? 'bg-blue-50 border-blue-200 text-blue-700':'bg-white'}`}>5. Brand</span>
        <span className={`px-2 py-1 rounded-md border ${step===6? 'bg-blue-50 border-blue-200 text-blue-700':'bg-white'}`}>6. Finish</span>
        <div className="ml-auto flex items-center gap-2">
          {step>1 && <button className="mm-btn" onClick={()=>setStep(step-1)}>Back</button>}
          {step<6 && <button className="mm-btn" onClick={()=>setStep(step+1)} disabled={nextDisabled}>Next</button>}
        </div>
      </div>

      {step === 1 && (
        <div className="mm-card p-6">
          <h2 className="text-lg font-semibold mb-2">Health Check</h2>
          <p className="text-sm text-gray-600 mb-3">We’ll quickly verify your system is ready. Database must be healthy to proceed. Redis can be Disabled in development.</p>
          <div className="flex flex-wrap gap-2 text-sm">
            <Badge ok={!!health?.db?.ok} label={`Database (${health?.db?.latency_ms ?? '—'} ms)`} />
            <Badge ok={!!health?.redis?.ok} label={`Redis ${health?.redis?.configured? (health?.redis?.ok? '(Healthy)':'(Issue)'):'(Disabled)'}`} />
          </div>
          <div className="text-xs text-gray-500 mt-2">Next enabled when Database is healthy.</div>
        </div>
      )}
      {step === 2 && (
        <div className="mm-card p-6">
          <h1 className="text-2xl font-semibold mb-2">Seed Demo Data</h1>
          <p className="text-gray-600">Populate the system so dashboards, pricing, and finance screens have data to show.</p>
          <div className="flex items-center gap-3 mt-4">
            <button onClick={() => seed(25)} disabled={busy} className={`mm-btn ${busy ? '' : 'primary'}`}>
              {busy ? 'Seeding…' : (seeded ? 'Reseed Demo Data' : 'Seed Demo Data')}
            </button>
            <a href="/" className="mm-btn">Go to Dashboard</a>
          </div>
          {msg && <div className="mt-3 text-sm text-gray-700">{msg}</div>}
        </div>
      )}

      {step === 3 && (
        <div className="mm-card p-6">
          <h2 className="text-lg font-semibold mb-2">Connect Integrations</h2>
          <div className="text-sm text-gray-700">
            Configured: {Object.values(health?.integrations||{}).filter((i:any)=>i?.configured).length} of {Object.keys(health?.integrations||{}).length}
          </div>
          <div className="mt-3 flex items-center gap-2">
            <a href="/integrations" className="mm-btn">Open Integrations</a>
            <a href="/" className="mm-btn">Skip for now</a>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="mm-card p-6">
          <h2 className="text-lg font-semibold mb-2">Run a Quick Simulation</h2>
          <p className="text-sm text-gray-600">Generate pricing proposals to review and approve in the Pricing Lab.</p>
          <div className="mt-3 flex items-center gap-2">
            <button onClick={() => runSim(25)} disabled={simBusy} className={`mm-btn ${simBusy ? '' : 'primary'}`}>{simBusy ? 'Starting…' : 'Run Simulation'}</button>
            <a href="/pricing" className="mm-btn">Open Pricing</a>
          </div>
          {simMsg && <div className="mt-3 text-sm text-gray-700">{simMsg}</div>}
        </div>
      )}

      {step === 5 && (
        <div className="mm-card p-6">
          <h2 className="text-lg font-semibold mb-2">Brand Your Console</h2>
          <p className="text-sm text-gray-600">Set a brand name and optional logo URL. We’ll use this in the sidebar header locally.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
            <label className="text-sm">
              <div className="text-gray-600 mb-1">Brand name</div>
              <input className="border rounded px-2 py-1 w-full" value={brandName} onChange={(e)=>setBrandName(e.target.value)} placeholder="Acme, Inc." />
            </label>
            <label className="text-sm">
              <div className="text-gray-600 mb-1">Logo URL (optional)</div>
              <input className="border rounded px-2 py-1 w-full" value={logoUrl} onChange={(e)=>setLogoUrl(e.target.value)} placeholder="https://.../logo.png" />
            </label>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <button className="mm-btn" onClick={saveBranding}>Save Branding</button>
            {brandSaved && <div className="text-xs text-gray-600">{brandSaved}</div>}
          </div>
        </div>
      )}

      {step === 6 && (
        <div className="mm-card p-6">
          <h2 className="text-lg font-semibold mb-2">All Set!</h2>
          <p className="text-sm text-gray-600">You can now explore the dashboard, Finance, and Pricing. Visit Integrations anytime to connect real data sources.</p>
          <div className="flex items-center gap-2 mt-3">
            <a href="/" className="mm-btn primary">Go to Dashboard</a>
            <a href="/finance" className="mm-btn">Open Finance</a>
            <a href="/pricing" className="mm-btn">Open Pricing</a>
          </div>
        </div>
      )}

      {step >= 3 && step <= 4 && (
        <div className="mm-card p-6">
          <h2 className="text-lg font-semibold mb-2">Current Data Status</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-sm">
            {['products','offers','history','sims','invoices','forecast'].map((k)=> (
              <div key={k} className="p-3 bg-gray-50 rounded border">
                <div className="text-xs text-gray-600">{k}</div>
                <div className="text-base font-semibold">{status?.[k] ?? '—'}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {step >= 3 && (
        <div className="mm-card p-6">
          <h2 className="text-lg font-semibold mb-2">Next Steps</h2>
          <ul className="list-disc pl-6 text-sm text-gray-700 space-y-1">
            <li>Open the <a href="/pricing" className="text-blue-600 hover:underline">Pricing Lab</a> to simulate prices.</li>
            <li>Visit <a href="/command-center" className="text-blue-600 hover:underline">Command Center</a> for AI decisions.</li>
            <li>Check <a href="/integrations" className="text-blue-600 hover:underline">Integrations</a> to connect real data sources.</li>
          </ul>
        </div>
      )}
      {/* Local Badge component for Health step */}
      <style jsx>{``}</style>
    </div>
  );
}

function Badge({ ok, label }: { ok: boolean; label: string }){
  return (
    <span className={`inline-block px-2 py-1 rounded-md border ${ok? 'bg-emerald-50 border-emerald-200 text-emerald-700':'bg-red-50 border-red-200 text-red-700'}`}>
      {label}: {ok? 'OK':'FAIL'}
    </span>
  );
}
