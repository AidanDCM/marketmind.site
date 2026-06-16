import { useState } from "react";
import { scoreProduct, type ProductInput, type ScoreResult } from "../api/client";
import { ScoreResultView } from "./ScoreResultView";

const DEFAULTS: ProductInput = {
  product_name: "",
  est_sale_price: 49,
  est_product_cost: 12,
  est_shipping_cost: 5,
  competition: 0.5,
  return_risk: 0.3,
  compliance_risk: 0.0,
  content_potential: 0.5,
  repeat_purchase_potential: 0.3,
  personal_fit: 0.5,
  supplier_reliability: 0.5,
  evidence_quality: 0.3,
  niche: "",
};

function Slider({ label, name, value, onChange }: {
  label: string; name: keyof ProductInput; value: number; onChange: (k: keyof ProductInput, v: number) => void;
}) {
  return (
    <div className="field">
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <label>{label}</label>
        <span className="range-val">{(value * 10).toFixed(1)}</span>
      </div>
      <input type="range" min={0} max={1} step={0.05} value={value}
        onChange={e => onChange(name, parseFloat(e.target.value))} />
    </div>
  );
}

export function ScoreProduct() {
  const [form, setForm] = useState<ProductInput>(DEFAULTS);
  const [result, setResult] = useState<ScoreResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setField<K extends keyof ProductInput>(k: K, v: ProductInput[K]) {
    setForm(f => ({ ...f, [k]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.product_name.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try { setResult(await scoreProduct(form)); }
    catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Score a Product</h2>
        <p>Evaluate unit economics and market fit before committing budget</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <form onSubmit={submit}>
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Product Details</div>
            <div className="field">
              <label>Product Name *</label>
              <input type="text" value={form.product_name} placeholder="e.g. Car Interior Refresh Kit"
                onChange={e => setField("product_name", e.target.value)} required />
            </div>
            <div className="field">
              <label>Niche</label>
              <input type="text" value={form.niche} placeholder="e.g. automotive accessories"
                onChange={e => setField("niche", e.target.value)} />
            </div>
            <div className="field-row">
              <div className="field" style={{ marginBottom: 0 }}>
                <label>Sale Price ($)</label>
                <input type="number" min={0} step={0.01} value={form.est_sale_price}
                  onChange={e => setField("est_sale_price", parseFloat(e.target.value) || 0)} />
              </div>
              <div className="field" style={{ marginBottom: 0 }}>
                <label>Product Cost ($)</label>
                <input type="number" min={0} step={0.01} value={form.est_product_cost}
                  onChange={e => setField("est_product_cost", parseFloat(e.target.value) || 0)} />
              </div>
            </div>
            <div className="field" style={{ marginTop: 14 }}>
              <label>Shipping Cost ($)</label>
              <input type="number" min={0} step={0.01} value={form.est_shipping_cost}
                onChange={e => setField("est_shipping_cost", parseFloat(e.target.value) || 0)} />
            </div>
          </div>

          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Risk & Fit Signals (0 = low, 10 = high)</div>
            <Slider label="Competition" name="competition" value={form.competition} onChange={setField} />
            <Slider label="Return Risk" name="return_risk" value={form.return_risk} onChange={setField} />
            <Slider label="Compliance Risk" name="compliance_risk" value={form.compliance_risk} onChange={setField} />
            <Slider label="Content Potential" name="content_potential" value={form.content_potential} onChange={setField} />
            <Slider label="Repeat Purchase Potential" name="repeat_purchase_potential" value={form.repeat_purchase_potential} onChange={setField} />
            <Slider label="Personal Fit" name="personal_fit" value={form.personal_fit} onChange={setField} />
            <Slider label="Supplier Reliability" name="supplier_reliability" value={form.supplier_reliability} onChange={setField} />
            <Slider label="Evidence Quality" name="evidence_quality" value={form.evidence_quality} onChange={setField} />
          </div>

          {error && <div className="alert alert-error" style={{ marginBottom: 12 }}>{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading || !form.product_name.trim()} style={{ width: "100%", padding: "11px" }}>
            {loading ? "Scoring…" : "Score Product"}
          </button>
        </form>

        <div>
          {loading && <div className="loading-row"><div className="spinner" /></div>}
          {result && <ScoreResultView result={result} />}
          {!result && !loading && (
            <div className="empty" style={{ paddingTop: 80 }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <p>Fill in the form to score a product</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
