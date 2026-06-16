import { useState } from "react";
import { prepareOffer, type PrepareOfferRequest, type ApprovalRecord } from "../api/client";

interface FormState {
  product_name: string;
  sale_price: number;
  key_benefit: string;
  target_customer: string;
  secondary_benefits: string;
  common_objections: string;
  shipping_note: string;
  return_policy: string;
  niche: string;
  channel: string;
  vendor: string;
  product_type: string;
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
  channel: "stripe",
  vendor: "MarketMind",
  product_type: "",
};

function lines(s: string): string[] {
  return s.split("\n").map(x => x.trim()).filter(Boolean);
}

export function PrepareOffer() {
  const [form, setForm] = useState<FormState>(DEFAULTS);
  const [result, setResult] = useState<ApprovalRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setField<K extends keyof FormState>(k: K, v: FormState[K]) {
    setForm(f => ({ ...f, [k]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.product_name.trim() || !form.key_benefit.trim() || !form.target_customer.trim()) return;
    setLoading(true); setError(null); setResult(null);
    const payload: PrepareOfferRequest = {
      product_name: form.product_name,
      sale_price: form.sale_price,
      key_benefit: form.key_benefit,
      target_customer: form.target_customer,
      secondary_benefits: lines(form.secondary_benefits),
      common_objections: lines(form.common_objections),
      shipping_note: form.shipping_note,
      return_policy: form.return_policy,
      niche: form.niche,
      channel: form.channel,
      vendor: form.vendor,
      product_type: form.product_type,
    };
    try { setResult(await prepareOffer(payload)); }
    catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Prepare Offer</h2>
        <p>Turn an offer into a queued approval the executor can run after you approve it</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <form onSubmit={submit}>
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Offer</div>
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
                <label>Channel</label>
                <select value={form.channel} onChange={e => setField("channel", e.target.value)}>
                  <option value="stripe">Stripe payment link</option>
                  <option value="shopify">Shopify product</option>
                </select>
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
              <textarea rows={2} value={form.secondary_benefits}
                onChange={e => setField("secondary_benefits", e.target.value)} />
            </div>
            <div className="field">
              <label>Common Objections (one per line)</label>
              <textarea rows={2} value={form.common_objections}
                onChange={e => setField("common_objections", e.target.value)} />
            </div>
          </div>

          {error && <div className="alert alert-error" style={{ marginBottom: 12 }}>{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading} style={{ width: "100%", padding: "11px" }}>
            {loading ? "Preparing…" : "Prepare Offer → Queue Approval"}
          </button>
        </form>

        <div>
          {loading && <div className="loading-row"><div className="spinner" /></div>}

          {result && (
            <>
              <div className="verdict review">
                <div className="verdict-label">Queued for Approval</div>
                <div className="verdict-value" style={{ fontSize: 20 }}>{result.status.toUpperCase()}</div>
                <div className="verdict-score">{result.action.replace(/_/g, " ")}</div>
              </div>
              <div className="card">
                <div className="card-title">Approval Record</div>
                <div className="approval-detail">
                  <div><div className="detail-label">Approval ID</div><div className="detail-value">{result.approval_id}</div></div>
                  <div><div className="detail-label">Risk</div><div className="detail-value">{result.risk_level}</div></div>
                  <div style={{ gridColumn: "1 / -1" }}>
                    <div className="detail-label">Summary</div><div className="detail-value">{result.summary}</div>
                  </div>
                  <div style={{ gridColumn: "1 / -1" }}>
                    <div className="detail-label">Rollback Plan</div><div className="detail-value">{result.rollback_plan}</div>
                  </div>
                </div>
                <div className="spec-text" style={{ marginTop: 12, color: "var(--text-muted)", fontSize: 12 }}>
                  Next: go to the Approval Queue, approve this record, then Execute (dry-run).
                </div>
              </div>
            </>
          )}

          {!result && !loading && (
            <div className="empty" style={{ paddingTop: 80 }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              <p>Fill in an offer to queue it for approval</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
