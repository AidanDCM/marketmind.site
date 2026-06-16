import { useState } from "react";
import { calculateEconomics, type EconomicsInput, type EconomicsResult } from "../api/client";

const DEFAULTS: EconomicsInput = {
  product_name: "",
  sale_price: 59,
  product_cost: 18,
  packaging_cost: 2,
  shipping_cost: 5,
  platform_fee: 0,
  payment_fee: 2,
  refund_allowance: 1,
  software_allocation: 0,
  estimated_cac: 12,
};

const COST_FIELDS: { label: string; key: keyof EconomicsInput }[] = [
  { label: "Sale Price ($)", key: "sale_price" },
  { label: "Product Cost ($)", key: "product_cost" },
  { label: "Packaging ($)", key: "packaging_cost" },
  { label: "Shipping ($)", key: "shipping_cost" },
  { label: "Platform Fee ($)", key: "platform_fee" },
  { label: "Payment Fee ($)", key: "payment_fee" },
  { label: "Refund Allowance ($)", key: "refund_allowance" },
  { label: "Software Alloc. ($)", key: "software_allocation" },
  { label: "Estimated CAC ($)", key: "estimated_cac" },
];

function fmt$(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 });
}

function actionClass(action: string): string {
  if (action === "reject" || action === "kill_product" || action === "pause_ads") return "reject";
  if (action.includes("approval") || action === "revise_offer") return "review";
  return "pass";
}

export function UnitEconomics() {
  const [form, setForm] = useState<EconomicsInput>(DEFAULTS);
  const [result, setResult] = useState<EconomicsResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setField<K extends keyof EconomicsInput>(k: K, v: EconomicsInput[K]) {
    setForm(f => ({ ...f, [k]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.product_name.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try { setResult(await calculateEconomics(form)); }
    catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Unit Economics</h2>
        <p>First-order margin and break-even CAC from the math engine</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <form onSubmit={submit}>
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Product</div>
            <div className="field">
              <label>Product Name *</label>
              <input type="text" value={form.product_name} placeholder="e.g. Interior Refresh Kit"
                onChange={e => setField("product_name", e.target.value)} required />
            </div>
          </div>

          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Cost Structure (per unit)</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {COST_FIELDS.map(f => (
                <div className="field" key={f.key} style={{ marginBottom: 0 }}>
                  <label>{f.label}</label>
                  <input type="number" min={0} step={0.01} value={form[f.key] as number}
                    onChange={e => setField(f.key, (parseFloat(e.target.value) || 0) as never)} />
                </div>
              ))}
            </div>
          </div>

          {error && <div className="alert alert-error" style={{ marginBottom: 12 }}>{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading || !form.product_name.trim()} style={{ width: "100%", padding: "11px" }}>
            {loading ? "Calculating…" : "Calculate"}
          </button>
        </form>

        <div>
          {loading && <div className="loading-row"><div className="spinner" /></div>}

          {result && (
            <>
              <div className={`verdict ${actionClass(result.recommended_action)}`}>
                <div className="verdict-label">Recommended Action</div>
                <div className="verdict-value" style={{ fontSize: 20 }}>
                  {result.recommended_action.replace(/_/g, " ").toUpperCase()}
                </div>
                <div className="verdict-score">{result.margin_status.replace(/_/g, " ")}</div>
              </div>

              <div className="metric-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
                <div className="metric-card">
                  <div className="metric-label">Break-even CAC</div>
                  <div className="metric-value">{fmt$(result.break_even_cac)}</div>
                  <div className="metric-sub">safe {fmt$(result.safe_cac_low)}–{fmt$(result.safe_cac_high)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Gross Profit / unit</div>
                  <div className={`metric-value ${result.gross_profit_before_ads >= 0 ? "metric-up" : "metric-down"}`}>
                    {fmt$(result.gross_profit_before_ads)}
                  </div>
                  <div className="metric-sub">before ads</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Gross Margin</div>
                  <div className="metric-value">{(result.gross_margin_before_ads * 100).toFixed(1)}%</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Contribution / unit</div>
                  <div className={`metric-value ${result.estimated_contribution_profit >= 0 ? "metric-up" : "metric-down"}`}>
                    {fmt$(result.estimated_contribution_profit)}
                  </div>
                  <div className="metric-sub">after est. CAC</div>
                </div>
              </div>

              <div className="card" style={{ marginBottom: 14 }}>
                <div className="card-title">Summary</div>
                <div className="spec-text">{result.reason_summary}</div>
              </div>

              {result.risks.length > 0 && (
                <div className="card">
                  <div className="card-title">Risks</div>
                  {result.risks.map((r, i) => (
                    <div key={i} className="list-item"><div className="bullet risk" /><div className="list-text">{r.replace(/_/g, " ")}</div></div>
                  ))}
                </div>
              )}
            </>
          )}

          {!result && !loading && (
            <div className="empty" style={{ paddingTop: 80 }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
              <p>Enter a cost structure to calculate economics</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
