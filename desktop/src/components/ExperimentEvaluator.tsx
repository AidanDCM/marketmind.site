import { useState } from "react";
import { evaluateExperiment, type ExperimentInput, type ExperimentResult } from "../api/client";

const DEFAULTS: ExperimentInput = {
  experiment_id: "exp_001",
  product_name: "",
  break_even_cac: 25,
  qualified_visits: 500,
  orders: 12,
  total_ad_spend: 240,
  total_revenue: 708,
  refund_count: 0,
  actual_shipping_cost: 5,
  planned_shipping_cost: 5,
  add_to_cart_count: 60,
  consecutive_losing_periods: 0,
  budget_cap: 300,
};

const NUM_FIELDS: { label: string; key: keyof ExperimentInput; step?: number }[] = [
  { label: "Break-even CAC ($)", key: "break_even_cac", step: 0.01 },
  { label: "Qualified Visits", key: "qualified_visits" },
  { label: "Orders", key: "orders" },
  { label: "Total Ad Spend ($)", key: "total_ad_spend", step: 0.01 },
  { label: "Total Revenue ($)", key: "total_revenue", step: 0.01 },
  { label: "Refund Count", key: "refund_count" },
  { label: "Actual Shipping ($)", key: "actual_shipping_cost", step: 0.01 },
  { label: "Planned Shipping ($)", key: "planned_shipping_cost", step: 0.01 },
  { label: "Add-to-Cart Count", key: "add_to_cart_count" },
  { label: "Consecutive Losing Periods", key: "consecutive_losing_periods" },
  { label: "Budget Cap ($)", key: "budget_cap", step: 0.01 },
];

function rulingClass(ruling: string): string {
  if (ruling === "kill") return "reject";
  if (ruling === "pause_ads" || ruling === "revise_offer") return "review";
  if (ruling === "scale_requires_approval") return "review";
  return "pass";
}

export function ExperimentEvaluator() {
  const [form, setForm] = useState<ExperimentInput>(DEFAULTS);
  const [result, setResult] = useState<ExperimentResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setField<K extends keyof ExperimentInput>(k: K, v: ExperimentInput[K]) {
    setForm(f => ({ ...f, [k]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.product_name.trim() || !form.experiment_id.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try { setResult(await evaluateExperiment(form)); }
    catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Experiment Evaluator</h2>
        <p>Apply the kill / scale rule engine to a live experiment snapshot</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <form onSubmit={submit}>
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Experiment</div>
            <div className="field-row">
              <div className="field" style={{ marginBottom: 0 }}>
                <label>Experiment ID *</label>
                <input type="text" value={form.experiment_id}
                  onChange={e => setField("experiment_id", e.target.value)} required />
              </div>
              <div className="field" style={{ marginBottom: 0 }}>
                <label>Product Name *</label>
                <input type="text" value={form.product_name} placeholder="e.g. Interior Kit"
                  onChange={e => setField("product_name", e.target.value)} required />
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Observed Performance</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {NUM_FIELDS.map(f => (
                <div className="field" key={f.key} style={{ marginBottom: 0 }}>
                  <label>{f.label}</label>
                  <input type="number" min={0} step={f.step ?? 1} value={form[f.key] as number}
                    onChange={e => setField(f.key, (parseFloat(e.target.value) || 0) as never)} />
                </div>
              ))}
            </div>
          </div>

          {error && <div className="alert alert-error" style={{ marginBottom: 12 }}>{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading || !form.product_name.trim()} style={{ width: "100%", padding: "11px" }}>
            {loading ? "Evaluating…" : "Evaluate"}
          </button>
        </form>

        <div>
          {loading && <div className="loading-row"><div className="spinner" /></div>}

          {result && (
            <>
              <div className={`verdict ${rulingClass(result.ruling)}`}>
                <div className="verdict-label">Ruling — {result.product_name}</div>
                <div className="verdict-value" style={{ fontSize: 20 }}>
                  {result.ruling.replace(/_/g, " ").toUpperCase()}
                </div>
                {result.requires_approval && (
                  <div style={{ marginTop: 10 }}>
                    <span className="badge badge-high">requires approval</span>
                  </div>
                )}
              </div>

              <div className="card" style={{ marginBottom: 14 }}>
                <div className="card-title">Reasoning</div>
                <div className="spec-text">{result.reason_summary}</div>
              </div>

              {result.risks.length > 0 && (
                <div className="card">
                  <div className="card-title">Risk Signals</div>
                  {result.risks.map((r, i) => (
                    <div key={i} className="list-item"><div className="bullet risk" /><div className="list-text">{r.replace(/_/g, " ")}</div></div>
                  ))}
                </div>
              )}
            </>
          )}

          {!result && !loading && (
            <div className="empty" style={{ paddingTop: 80 }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
              <p>Enter a snapshot to get a kill/scale ruling</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
