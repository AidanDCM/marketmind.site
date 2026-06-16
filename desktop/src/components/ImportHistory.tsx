import { useEffect, useState } from "react";
import { getImportBatch, ImportBatch, ImportBatchDetail, listImportHistory } from "../api/client";

const SOURCE_LABELS: Record<string, string> = {
  stripe_charges: "Stripe Charges",
  shopify_orders: "Shopify Orders",
  shopify_products: "Shopify Products",
  stripe_webhook: "Stripe Webhook",
  shopify_webhook_order: "Shopify Webhook (Order)",
  csv_orders: "CSV Orders",
  csv_products: "CSV Products",
  csv_ad_report: "CSV Ad Report",
};

function label(source: string) {
  return SOURCE_LABELS[source] ?? source;
}

function BatchDetail({ batch }: { batch: ImportBatchDetail }) {
  if (batch.rows.length === 0) return <p className="dim">No rows in this batch.</p>;
  const cols = Object.keys(batch.rows[0]);
  return (
    <div style={{ overflowX: "auto", marginTop: "1rem" }}>
      <table className="data-table">
        <thead>
          <tr>{cols.map(c => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {batch.rows.map((r, i) => (
            <tr key={i}>{cols.map(c => <td key={c}>{r[c] ?? ""}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ImportHistory() {
  const [batches, setBatches] = useState<ImportBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ImportBatchDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [sourceFilter, setSourceFilter] = useState<string>("");

  function load() {
    setLoading(true);
    setError(null);
    listImportHistory(sourceFilter || undefined)
      .then(setBatches)
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [sourceFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  async function openBatch(id: number) {
    setDetailLoading(true);
    setSelected(null);
    try {
      setSelected(await getImportBatch(id));
    } finally {
      setDetailLoading(false);
    }
  }

  const sources = Array.from(new Set(batches.map(b => b.source)));

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem", marginBottom: "1.5rem" }}>
        <h2 style={{ margin: 0 }}>Import History</h2>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
          <select
            style={{ padding: "6px 10px", borderRadius: "6px", border: "1px solid var(--border)", background: "var(--surface-2)", color: "var(--text)", fontSize: "13px" }}
            value={sourceFilter}
            onChange={e => setSourceFilter(e.target.value)}
          >
            <option value="">All sources</option>
            {sources.map(s => <option key={s} value={s}>{label(s)}</option>)}
          </select>
          <button className="btn btn-secondary" onClick={load} disabled={loading}>
            {loading ? "Loading…" : "Refresh"}
          </button>
        </div>
      </div>

      <p className="dim" style={{ marginBottom: "1rem" }}>
        Every pull and webhook event is recorded here. Click a row to inspect its data.
      </p>

      {error && <div className="error-banner">{error}</div>}

      {!loading && batches.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
          <p className="dim">No import batches yet. Pull live data or configure webhooks to populate history.</p>
        </div>
      )}

      {batches.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Source</th>
                <th>Pulled at</th>
                <th>Total</th>
                <th style={{ color: "var(--green)" }}>OK</th>
                <th style={{ color: "var(--yellow)" }}>Review</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {batches.map(b => (
                <tr key={b.id} style={{ cursor: "pointer" }} onClick={() => openBatch(b.id)}>
                  <td className="dim">{b.id}</td>
                  <td><strong>{label(b.source)}</strong></td>
                  <td className="dim">{new Date(b.pulled_at).toLocaleString()}</td>
                  <td>{b.total_rows}</td>
                  <td style={{ color: "var(--green)" }}>{b.ok_count}</td>
                  <td style={{ color: b.review_count > 0 ? "var(--yellow)" : "var(--text-muted)" }}>{b.review_count}</td>
                  <td>
                    <button className="btn btn-secondary" style={{ padding: "4px 10px", fontSize: "12px" }} onClick={e => { e.stopPropagation(); openBatch(b.id); }}>
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(detailLoading || selected) && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          {detailLoading && <p className="dim">Loading rows…</p>}
          {selected && !detailLoading && (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <div>
                  <strong>{label(selected.source)}</strong>
                  <span className="dim" style={{ marginLeft: "0.75rem" }}>Batch #{selected.id} · {new Date(selected.pulled_at).toLocaleString()}</span>
                </div>
                <button className="btn btn-secondary" style={{ padding: "4px 10px", fontSize: "12px" }} onClick={() => setSelected(null)}>
                  Close
                </button>
              </div>
              <BatchDetail batch={selected} />
            </>
          )}
        </div>
      )}
    </div>
  );
}
