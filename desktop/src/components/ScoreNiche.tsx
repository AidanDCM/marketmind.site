import { useState } from "react";
import { scoreNiche, type NicheInput, type ScoreResult } from "../api/client";
import { ScoreResultView } from "./ScoreResultView";

const DEFAULTS: NicheInput = {
  niche_name: "",
  demand: 0.5,
  competition: 0.5,
  margin_potential: 0.5,
  content_potential: 0.5,
  personal_fit: 0.5,
  supplier_availability: 0.5,
  repeat_purchase_potential: 0.3,
  regulatory_risk: 0.0,
  evidence_quality: 0.3,
};

function Slider({ label, name, value, onChange }: {
  label: string; name: keyof NicheInput; value: number; onChange: (k: keyof NicheInput, v: number) => void;
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

export function ScoreNiche() {
  const [form, setForm] = useState<NicheInput>(DEFAULTS);
  const [result, setResult] = useState<ScoreResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setField<K extends keyof NicheInput>(k: K, v: NicheInput[K]) {
    setForm(f => ({ ...f, [k]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.niche_name.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try { setResult(await scoreNiche(form)); }
    catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Score a Niche</h2>
        <p>Evaluate a market opportunity before sourcing individual products</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <form onSubmit={submit}>
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Niche</div>
            <div className="field">
              <label>Niche Name *</label>
              <input type="text" value={form.niche_name} placeholder="e.g. automotive detailing"
                onChange={e => setField("niche_name", e.target.value)} required />
            </div>
          </div>

          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Market Signals (0 = low, 10 = high)</div>
            <Slider label="Demand" name="demand" value={form.demand} onChange={setField} />
            <Slider label="Competition" name="competition" value={form.competition} onChange={setField} />
            <Slider label="Margin Potential" name="margin_potential" value={form.margin_potential} onChange={setField} />
            <Slider label="Content Potential" name="content_potential" value={form.content_potential} onChange={setField} />
            <Slider label="Personal Fit" name="personal_fit" value={form.personal_fit} onChange={setField} />
            <Slider label="Supplier Availability" name="supplier_availability" value={form.supplier_availability} onChange={setField} />
            <Slider label="Repeat Purchase Potential" name="repeat_purchase_potential" value={form.repeat_purchase_potential} onChange={setField} />
            <Slider label="Regulatory Risk" name="regulatory_risk" value={form.regulatory_risk} onChange={setField} />
            <Slider label="Evidence Quality" name="evidence_quality" value={form.evidence_quality} onChange={setField} />
          </div>

          {error && <div className="alert alert-error" style={{ marginBottom: 12 }}>{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading || !form.niche_name.trim()} style={{ width: "100%", padding: "11px" }}>
            {loading ? "Scoring…" : "Score Niche"}
          </button>
        </form>

        <div>
          {loading && <div className="loading-row"><div className="spinner" /></div>}
          {result && <ScoreResultView result={result} />}
          {!result && !loading && (
            <div className="empty" style={{ paddingTop: 80 }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <p>Fill in the form to score a niche</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
