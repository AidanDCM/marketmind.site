"use client";

import useSWR from "swr";
import * as React from "react";
import { authHeaders } from "../../lib/api";
import { useToast } from "../../components/ui/Toast";
import { SkeletonText } from "../../components/ui/Skeleton";
import { Th, Td } from "../../components/ui/Table";
import { downloadCsv } from "../../lib/csv";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";
const fetcher = (url: string) => fetch(url, { headers: authHeaders() }).then((r) => r.json());

export default function ProfitPage() {
  const toast = useToast();
  const { data: kpis, error: kpisErr } = useSWR(`${API}/dash/kpis`, fetcher);
  const { data: profitLog, error: profitErr } = useSWR(`${API}/profit/log?limit=25`, fetcher);
  const { data: rollouts, error: rolloutsErr } = useSWR(`${API}/learning/rollouts?limit=5`, fetcher);

  const hasError = Boolean(kpisErr || profitErr || rolloutsErr);
  const prevHasErrorRef = React.useRef<boolean>(false);
  React.useEffect(() => {
    if (hasError && !prevHasErrorRef.current) {
      toast.error("Some Profit data is unavailable");
    } else if (!hasError && prevHasErrorRef.current) {
      toast.success("Profit data recovered");
    }
    prevHasErrorRef.current = hasError;
  }, [hasError, toast]);

  return (
    <main className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Profit</h1>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {kpis === undefined ? (
          [0,1,2].map((i) => (
            <div key={i} className="border rounded p-4">
              <h2 className="font-medium mb-2"><SkeletonText lines={1} /></h2>
              <div className="text-3xl"><SkeletonText lines={1} /></div>
            </div>
          ))
        ) : (
          <>
            <div className="border rounded p-4">
              <h2 className="font-medium mb-2">Publish Success %</h2>
              <p className="text-3xl">{kpis?.publish_success_pct ?? "–"}</p>
            </div>
            <div className="border rounded p-4">
              <h2 className="font-medium mb-2">VTR / ODR</h2>
              <p className="text-3xl">{kpis ? `${kpis.vtr_pct ?? "–"} / ${kpis.odr_pct ?? "–"}` : "–"}</p>
            </div>
            <div className="border rounded p-4">
              <h2 className="font-medium mb-2">Recon %</h2>
              <p className="text-3xl">{kpis?.recon_pct ?? "–"}</p>
            </div>
          </>
        )}
      </section>

      <section className="border rounded p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-medium">Profit Modules Log (latest)</h2>
          <button
            className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50"
            onClick={() => {
              const items = profitLog?.items ?? [];
              const headers = ["timestamp","module","action","guardrails","outcome"];
              const rows = items.map((r: any) => [
                r.timestamp ?? "",
                r.module ?? "",
                r.action ?? "",
                typeof r.guardrails === "string" ? r.guardrails : JSON.stringify(r.guardrails ?? {}),
                r.outcome ?? "",
              ]);
              downloadCsv("profit_log", headers, rows);
            }}
          >
            Export CSV
          </button>
        </div>
        <table className="w-full text-sm" aria-label="Profit modules table">
          <caption className="sr-only">Recent Profit module events</caption>
          <thead>
            <tr className="text-left">
              <Th>Time</Th>
              <Th>Module</Th>
              <Th>Action</Th>
              <Th>Guardrails</Th>
              <Th>Outcome</Th>
            </tr>
          </thead>
          <tbody>
            {profitLog?.items?.length ? (
              profitLog.items.map((r: any, i: number) => (
                <tr key={i} className="border-t">
                  <Td>{r.timestamp ?? "–"}</Td>
                  <Td>{r.module ?? "–"}</Td>
                  <Td>{r.action ?? "–"}</Td>
                  <Td>{typeof r.guardrails === "string" ? r.guardrails : JSON.stringify(r.guardrails ?? {})}</Td>
                  <Td>{r.outcome ?? "–"}</Td>
                </tr>
              ))
            ) : (
              <tr>
                <Td colSpan={5}>No entries yet.</Td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="border rounded p-4">
        <h2 className="font-medium mb-3">Learning Rollouts (shadow/canary/prod)</h2>
        <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
          {JSON.stringify(rollouts ?? { items: [] }, null, 2)}
        </pre>
      </section>

      <section className="border rounded p-4 space-y-3">
        <h2 className="font-medium">Operator: Promote Rollout</h2>
        <PromoteRolloutForm />
      </section>

      <section className="border rounded p-4 space-y-3">
        <h2 className="font-medium">Operator: Historical Train</h2>
        <HistoricalTrainForm />
      </section>
    </main>
  );
}

function PromoteRolloutForm() {
  const [rolloutId, setRolloutId] = React.useState<string>("");
  const [phase, setPhase] = React.useState<string>("canary");
  const [msg, setMsg] = React.useState<string>("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      const res = await fetch(`${API}/learning/rollouts/promote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rollout_id: Number(rolloutId), phase }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
      setMsg("Promote request accepted.");
    } catch (err: any) {
      setMsg(`Error: ${err?.message || String(err)}`);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-2">
      <div className="flex gap-2 items-center">
        <label className="w-32">Rollout ID</label>
        <input
          className="border rounded px-2 py-1"
          value={rolloutId}
          onChange={(e) => setRolloutId(e.target.value)}
          placeholder="e.g., 1"
          required
        />
      </div>
      <div className="flex gap-2 items-center">
        <label className="w-32">Phase</label>
        <select
          className="border rounded px-2 py-1"
          value={phase}
          onChange={(e) => setPhase(e.target.value)}
        >
          <option value="canary">canary</option>
          <option value="prod">prod</option>
        </select>
      </div>
      <div className="flex gap-2 items-center">
        <button type="submit" className="bg-blue-600 text-white px-3 py-1 rounded">
          Promote
        </button>
        {msg && <span className="text-sm">{msg}</span>}
      </div>
    </form>
  );
}
