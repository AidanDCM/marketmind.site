"use client";

import useSWR from "swr";
import * as React from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";
const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function IncidentsPage() {
  const { data: health } = useSWR(`${API}/health/summary`, fetcher);
  const { data: orch } = useSWR(`${API}/orchestrator/health`, fetcher);
  const incidents = (health?.incidents ?? []) as any[];

  return (
    <main className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Incidents</h1>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="border rounded p-4">
          <h2 className="font-medium mb-2">Publish Success %</h2>
          <p className="text-3xl">{health?.publish_success_pct ?? "–"}</p>
        </div>
        <div className="border rounded p-4">
          <h2 className="font-medium mb-2">VTR / ODR</h2>
          <p className="text-3xl">{health ? `${health.vtr_pct ?? "–"} / ${health.odr_pct ?? "–"}` : "–"}</p>
        </div>
        <div className="border rounded p-4">
          <h2 className="font-medium mb-2">Recon %</h2>
          <p className="text-3xl">{health?.recon_pct ?? "–"}</p>
        </div>
      </section>

      <section className="border rounded p-4">
        <h2 className="font-medium mb-3">Freeze States</h2>
        <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
          {JSON.stringify(orch ?? {}, null, 2)}
        </pre>
      </section>

      <section className="border rounded p-4">
        <h2 className="font-medium mb-3">Open Incidents</h2>
        {incidents.length ? (
          <ul className="list-disc pl-6 space-y-1">
            {incidents.map((it: any, idx: number) => (
              <li key={idx}>
                <span className="font-medium">{it.kind ?? "incident"}</span>: {it.message ?? JSON.stringify(it)}
              </li>
            ))}
          </ul>
        ) : (
          <p>No open incidents.</p>
        )}
      </section>

      <section className="border rounded p-4 space-y-3">
        <h2 className="font-medium">Operator: Freeze/Unfreeze Brain</h2>
        <FreezeForm />
      </section>
    </main>
  );
}

function FreezeForm() {
  const [brain, setBrain] = React.useState<string>("pricing");
  const [freeze, setFreeze] = React.useState<string>("true");
  const [msg, setMsg] = React.useState<string>("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      const res = await fetch(`${API}/orchestrator/freeze/${brain}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ freeze: freeze === "true" }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
      setMsg(`OK: ${freeze === "true" ? "Frozen" : "Unfrozen"} ${brain}`);
    } catch (err: any) {
      setMsg(`Error: ${err?.message || String(err)}`);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-2">
      <div className="flex gap-2 items-center">
        <label className="w-32">Brain</label>
        <select className="border rounded px-2 py-1" value={brain} onChange={(e) => setBrain(e.target.value)}>
          <option value="pricing">pricing</option>
          <option value="marketing">marketing</option>
          <option value="analytics">analytics</option>
          <option value="compliance">compliance</option>
          <option value="expansion">expansion</option>
        </select>
      </div>
      <div className="flex gap-2 items-center">
        <label className="w-32">Action</label>
        <select className="border rounded px-2 py-1" value={freeze} onChange={(e) => setFreeze(e.target.value)}>
          <option value="true">Freeze</option>
          <option value="false">Unfreeze</option>
        </select>
      </div>
      <div className="flex gap-2 items-center">
        <button type="submit" className="bg-blue-600 text-white px-3 py-1 rounded">Apply</button>
        {msg && <span className="text-sm">{msg}</span>}
      </div>
    </form>
  );
}
