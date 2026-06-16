import { useState } from "react";
import { generateSpec, type SpecRequest, type OfferSpec } from "../api/client";

interface FormState {
  product_name: string;
  sale_price: number;
  key_benefit: string;
  target_customer: string;
  secondary_benefits: string;   // newline-separated in the UI
  common_objections: string;    // newline-separated in the UI
  shipping_note: string;
  return_policy: string;
  niche: string;
}

const DEFAULTS: FormState = {
  product_name: "",
  sale_price: 59,
  key_benefit: "",
  target_customer: "",
  secondary_benefits: "",
  common_objections: "",
  shipping_note: "",
  return_policy: "",
  niche: "",
};

function lines(s: string): string[] {
  return s.split("\n").map(x => x.trim()).filter(Boolean);
}

export function OfferSpecPage() {
  const [form, setForm] = useState<FormState>(DEFAULTS);
  const [spec, setSpec] = useState<OfferSpec | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setField<K extends keyof FormState>(k: K, v: FormState[K]) {
    setForm(f => ({ ...f, [k]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.product_name.trim() || !form.key_benefit.trim() || !form.target_customer.trim()) return;
    setLoading(true); setError(null); setSpec(null);
    const payload: SpecRequest = {
      product_name: form.product_name,
      sale_price: form.sale_price,
      key_benefit: form.key_benefit,
      target_customer: form.target_customer,
      secondary_benefits: lines(form.secondary_benefits),
      common_objections: lines(form.common_objections),
      shipping_note: form.shipping_note,
      return_policy: form.return_policy,
      niche: form.niche,
    };
    try { setSpec(await generateSpec(payload)); }
    catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Offer Spec Generator</h2>
        <p>Generate a Codex-ready landing-page spec from honest inputs only</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: 20 }}>
        <form onSubmit={submit}>
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Offer Context</div>
            <div className="field">
              <label>Product Name *</label>
              <input type="text" value={form.product_name} placeholder="e.g. Interior Refresh Kit"
                onChange={e => setField("product_name", e.target.value)} required />
            </div>
            <div className="field-row">
              <div className="field" style={{ marginBottom: 0 }}>
                <label>Sale Price ($)</label>
                <input type="number" min={0} step={0.01} value={form.sale_price}
                  onChange={e => setField("sale_price", parseFloat(e.target.value) || 0)} />
              </div>
              <div className="field" style={{ marginBottom: 0 }}>
                <label>Niche</label>
                <input type="text" value={form.niche}
                  onChange={e => setField("niche", e.target.value)} />
              </div>
            </div>
            <div className="field" style={{ marginTop: 14 }}>
              <label>Key Benefit *</label>
              <input type="text" value={form.key_benefit} placeholder="single honest value proposition"
                onChange={e => setField("key_benefit", e.target.value)} required />
            </div>
            <div className="field">
              <label>Target Customer *</label>
              <input type="text" value={form.target_customer} placeholder="who this is for"
                onChange={e => setField("target_customer", e.target.value)} required />
            </div>
            <div className="field">
              <label>Secondary Benefits (one per line)</label>
              <textarea rows={3} value={form.secondary_benefits}
                onChange={e => setField("secondary_benefits", e.target.value)} />
            </div>
            <div className="field">
              <label>Common Objections (one per line)</label>
              <textarea rows={3} value={form.common_objections}
                onChange={e => setField("common_objections", e.target.value)} />
            </div>
            <div className="field-row">
              <div className="field" style={{ marginBottom: 0 }}>
                <label>Shipping Note</label>
                <input type="text" value={form.shipping_note} placeholder="Ships in 5-7 days"
                  onChange={e => setField("shipping_note", e.target.value)} />
              </div>
              <div className="field" style={{ marginBottom: 0 }}>
                <label>Return Policy</label>
                <input type="text" value={form.return_policy} placeholder="30-day returns"
                  onChange={e => setField("return_policy", e.target.value)} />
              </div>
            </div>
          </div>

          {error && <div className="alert alert-error" style={{ marginBottom: 12 }}>{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading} style={{ width: "100%", padding: "11px" }}>
            {loading ? "Generating…" : "Generate Spec"}
          </button>
        </form>

        <div>
          {loading && <div className="loading-row"><div className="spinner" /></div>}

          {spec && (
            <>
              <div className="card spec-block">
                <div className="spec-section-title">Hero</div>
                <div className="spec-text" style={{ fontWeight: 700, fontSize: 16 }}>{spec.headline}</div>
                <div className="spec-text" style={{ color: "var(--text-muted)", marginTop: 4 }}>{spec.subheadline}</div>
              </div>

              <div className="card spec-block">
                <div className="spec-section-title">What's Included</div>
                {spec.bundle_items.map((b, i) => (
                  <div key={i} className="list-item">
                    <div className="bullet rec" />
                    <div className="list-text"><strong>{b.name}</strong> — {b.description}</div>
                  </div>
                ))}
              </div>

              <div className="card spec-block">
                <div className="spec-section-title">FAQ</div>
                {spec.faq.map((f, i) => (
                  <div key={i} style={{ marginBottom: 10 }}>
                    <div className="spec-text" style={{ fontWeight: 600 }}>{f.question}</div>
                    <div className="spec-text" style={{ color: "var(--text-muted)" }}>{f.answer}</div>
                  </div>
                ))}
              </div>

              <div className="card spec-block">
                <div className="spec-section-title">Call to Action</div>
                <div className="spec-text">{spec.cta_primary}</div>
                <div style={{ marginTop: 10 }}>
                  <span className="btn-primary" style={{ display: "inline-block", padding: "8px 16px", cursor: "default" }}>
                    {spec.cta_button_label}
                  </span>
                </div>
              </div>

              <div className="card spec-block">
                <div className="spec-section-title">Trust Signals</div>
                {spec.trust_signals.map((t, i) => <span key={i} className="spec-tag">{t}</span>)}
              </div>

              <div className="card spec-block">
                <div className="spec-section-title">Safety Flags (must NOT appear)</div>
                {spec.safety_flags.map((s, i) => (
                  <span key={i} className="spec-tag" style={{ color: "var(--red)", borderColor: "rgba(239,68,68,0.3)" }}>
                    {s.replace(/_/g, " ")}
                  </span>
                ))}
              </div>

              <div className="card spec-block">
                <div className="spec-section-title">Codex Build Notes</div>
                <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: "var(--text-muted)", fontFamily: "inherit", lineHeight: 1.5 }}>
                  {spec.codex_build_notes}
                </pre>
              </div>
            </>
          )}

          {!spec && !loading && (
            <div className="empty" style={{ paddingTop: 80 }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              <p>Fill in the offer context to generate a spec</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
