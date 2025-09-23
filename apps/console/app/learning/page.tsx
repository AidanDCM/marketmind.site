"use client";

import * as React from "react";
import useSWR from "swr";
import { authHeaders } from "../../lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";
const fetcher = (url: string) => fetch(url, { headers: authHeaders() }).then((r) => r.json());

export default function LearningPage() {
  const { data: models } = useSWR(`${API}/learning/models?limit=25`, fetcher);
  const { data: metrics } = useSWR(`${API}/learning/metrics?limit=25`, fetcher);
  const { data: drift } = useSWR(`${API}/learning/drift?limit=25`, fetcher);
  const { data: benchmarks } = useSWR(`${API}/learning/benchmarks?limit=25`, fetcher);
  const { data: rollouts } = useSWR(`${API}/learning/rollouts?limit=25`, fetcher);

  return (
    <main className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Learning</h1>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <InfoCard title="Models" value={models?.total ?? "–"} />
        <InfoCard title="Metrics" value={metrics?.total ?? "–"} />
        <InfoCard title="Rollouts" value={rollouts?.total ?? "–"} />
      </section>

      <section className="border rounded p-4">
        <h2 className="font-medium mb-3">Model Versions</h2>
        <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
          {JSON.stringify(models ?? { items: [] }, null, 2)}
        </pre>
      </section>

      <section className="border rounded p-4">
        <h2 className="font-medium mb-3">Metrics</h2>
        <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
          {JSON.stringify(metrics ?? { items: [] }, null, 2)}
        </pre>
      </section>

      <section className="border rounded p-4">
        <h2 className="font-medium mb-3">Drift Reports</h2>
        <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
          {JSON.stringify(drift ?? { items: [] }, null, 2)}
        </pre>
      </section>

      <section className="border rounded p-4">
        <h2 className="font-medium mb-3">Benchmarks</h2>
        <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
          {JSON.stringify(benchmarks ?? { items: [] }, null, 2)}
        </pre>
      </section>

      <section className="border rounded p-4">
        <h2 className="font-medium mb-3">Rollouts</h2>
        <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
          {JSON.stringify(rollouts ?? { items: [] }, null, 2)}
        </pre>
      </section>

      <section className="border rounded p-4 space-y-3">
        <h2 className="font-medium">Operator: Retrain (dataset_range)</h2>
        <RetrainForm />
      </section>

      <section className="border rounded p-4 space-y-3">
        <h2 className="font-medium">Operator: Historical Train</h2>
        <HistoricalTrainForm />
      </section>
    </main>
  );
}

function InfoCard({ title, value }: { title: string; value: React.ReactNode }) {
  return (
    <div className="border rounded p-4">
      <h3 className="font-medium mb-2">{title}</h3>
      <p className="text-3xl">{value}</p>
    </div>
  );
}

function RetrainForm() {
  const [brain, setBrain] = React.useState<string>("pricing");
  const [range, setRange] = React.useState<string>("2024-01-01..2024-01-31");
  const [msg, setMsg] = React.useState<string>("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      const res = await fetch(`${API}/learning/models/retrain`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ brain, dataset_range: range }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
      setMsg("Retrain request accepted.");
    } catch (err: any) {
      setMsg(`Error: ${err?.message || String(err)}`);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-2">
      <div className="flex gap-2 items-center">
        <label className="w-40">Brain</label>
        <input className="border rounded px-2 py-1" value={brain} onChange={(e) => setBrain(e.target.value)} />
      </div>
      <div className="flex gap-2 items-center">
        <label className="w-40">Dataset Range</label>
        <input className="border rounded px-2 py-1" value={range} onChange={(e) => setRange(e.target.value)} />
      </div>
      <div className="flex gap-2 items-center">
        <button type="submit" className="bg-blue-600 text-white px-3 py-1 rounded">Retrain</button>
        {msg && <span className="text-sm">{msg}</span>}
      </div>
    </form>
  );
}

function HistoricalTrainForm() {
  const [brainId, setBrainId] = React.useState<string>("pricing");
  const [startDate, setStartDate] = React.useState<string>("2024-01-01T00:00:00Z");
  const [endDate, setEndDate] = React.useState<string>("2024-01-31T23:59:59Z");
  const [features, setFeatures] = React.useState<string>("price,clicks");
  const [modelType, setModelType] = React.useState<string>("auto");
  const [msg, setMsg] = React.useState<string>("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      const res = await fetch(`${API}/learning/train/historical`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          brain_id: brainId,
          start_date: startDate,
          end_date: endDate,
          features: features.split(",").map((s) => s.trim()).filter(Boolean),
          model_type: modelType,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
      setMsg("Historical train request accepted.");
    } catch (err: any) {
      setMsg(`Error: ${err?.message || String(err)}`);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-2">
      <div className="flex gap-2 items-center">
        <label className="w-40">Brain</label>
        <input className="border rounded px-2 py-1" value={brainId} onChange={(e) => setBrainId(e.target.value)} />
      </div>
      <div className="flex gap-2 items-center">
        <label className="w-40">Start</label>
        <input className="border rounded px-2 py-1" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
      </div>
      <div className="flex gap-2 items-center">
        <label className="w-40">End</label>
        <input className="border rounded px-2 py-1" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
      </div>
      <div className="flex gap-2 items-center">
        <label className="w-40">Features</label>
        <input className="border rounded px-2 py-1" value={features} onChange={(e) => setFeatures(e.target.value)} />
      </div>
      <div className="flex gap-2 items-center">
        <label className="w-40">Model Type</label>
        <select className="border rounded px-2 py-1" value={modelType} onChange={(e) => setModelType(e.target.value)}>
          <option value="auto">auto</option>
          <option value="gbm">gbm</option>
          <option value="xgb">xgb</option>
          <option value="nn">nn</option>
        </select>
      </div>
      <div className="flex gap-2 items-center">
        <button type="submit" className="bg-blue-600 text-white px-3 py-1 rounded">Train Historical</button>
        {msg && <span className="text-sm">{msg}</span>}
      </div>
    </form>
  );
}
