import { useState } from "react";
import { prepareSupplierOutreach, fetchOutreachDraft, type ApprovalRecord } from "../api/client";

export function SupplierOutreach() {
  const [supplier, setSupplier] = useState("");
  const [product, setProduct] = useState("");
  const [qty, setQty] = useState(1);
  const [cost, setCost] = useState("");
  const [note, setNote] = useState("");
  const [result, setResult] = useState<ApprovalRecord | null>(null);
  const [draft, setDraft] = useState<Record<string, unknown> | null>(null);  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    prepareSupplierOutreach({
      supplier_name: supplier,
      product_name: product,
      sample_quantity: qty,
      target_unit_cost: cost ? parseFloat(cost) : undefined,
      operator_note: note,
    })
      .then(r => {
        setResult(r);
        return fetchOutreachDraft(r.approval_id).catch(() => null);
      })
      .then(d => { if (d) setDraft(d); })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Supplier Outreach</h2>
        <p>Draft a sample-order email and queue a contact_supplier approval (dry-run).</p>
      </div>
      <form onSubmit={submit} className="card" style={{ maxWidth: 520 }}>
        {[
          ["Supplier name", supplier, setSupplier, "text"],
          ["Product name", product, setProduct, "text"],
          ["Target unit cost ($)", cost, setCost, "number"],
          ["Operator note", note, setNote, "text"],
        ].map(([label, val, set, type]) => (
          <label key={label as string} style={{ display: "block", marginBottom: 12 }}>
            <div className="detail-label">{label as string}</div>
            <input
              type={type as string}
              value={val as string}
              onChange={e => (set as (v: string) => void)(e.target.value)}
              required={label === "Supplier name" || label === "Product name"}
              style={{ width: "100%" }}
            />
          </label>
        ))}
        <label style={{ display: "block", marginBottom: 12 }}>
          <div className="detail-label">Sample quantity</div>
          <input type="number" min={1} value={qty} onChange={e => setQty(parseInt(e.target.value, 10) || 1)} />
        </label>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Preparing…" : "Prepare outreach approval"}
        </button>
      </form>
      {error && <div className="alert alert-error" style={{ marginTop: 14 }}>{error}</div>}
      {result && (
        <div className="alert alert-ok" style={{ marginTop: 14 }}>
          Queued approval <code>{result.approval_id}</code> — status: {result.status}
          {draft && typeof draft.subject === "string" && (
            <p style={{ margin: "8px 0 0" }}>Subject preview: <em>{draft.subject}</em></p>
          )}
        </div>
      )}
    </div>
  );
}
