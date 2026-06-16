import { useState } from "react";
import {
  fetchStripeOrders,
  fetchShopifyOrders,
  fetchShopifyProducts,
  ImportResult,
} from "../api/client";

type SourceKey = "stripe_orders" | "shopify_orders" | "shopify_products";

const SOURCES: { key: SourceKey; label: string; note: string }[] = [
  { key: "stripe_orders", label: "Stripe Charges", note: "Requires STRIPE_API_KEY on the server" },
  { key: "shopify_orders", label: "Shopify Orders", note: "Requires SHOPIFY_STORE_DOMAIN + SHOPIFY_ACCESS_TOKEN" },
  { key: "shopify_products", label: "Shopify Products", note: "Requires SHOPIFY_STORE_DOMAIN + SHOPIFY_ACCESS_TOKEN" },
];

function fetch(key: SourceKey): Promise<ImportResult> {
  if (key === "stripe_orders") return fetchStripeOrders();
  if (key === "shopify_orders") return fetchShopifyOrders();
  return fetchShopifyProducts();
}

function ResultTable({ result }: { result: ImportResult }) {
  const rows = result.ok_rows;
  if (rows.length === 0) return <p className="dim">No rows returned.</p>;
  const cols = Object.keys(rows[0].data);
  return (
    <div style={{ overflowX: "auto" }}>
      <table className="data-table">
        <thead>
          <tr>
            {cols.map(c => <th key={c}>{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {cols.map(c => <td key={c}>{r.data[c] ?? ""}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
      {result.review_count > 0 && (
        <p className="dim" style={{ marginTop: "0.5rem" }}>
          {result.review_count} row(s) skipped during normalization (malformed / missing fields).
        </p>
      )}
    </div>
  );
}

export function LiveData() {
  const [active, setActive] = useState<SourceKey>("stripe_orders");
  const [results, setResults] = useState<Partial<Record<SourceKey, ImportResult>>>({});
  const [errors, setErrors] = useState<Partial<Record<SourceKey, string>>>({});
  const [loading, setLoading] = useState<SourceKey | null>(null);

  async function pull(key: SourceKey) {
    setLoading(key);
    setErrors(e => ({ ...e, [key]: undefined }));
    try {
      const data = await fetch(key);
      setResults(r => ({ ...r, [key]: data }));
    } catch (err) {
      setErrors(e => ({ ...e, [key]: (err as Error).message }));
    } finally {
      setLoading(null);
    }
  }

  const src = SOURCES.find(s => s.key === active)!;
  const result = results[active];
  const error = errors[active];

  return (
    <div>
      <h2>Live Data Sources</h2>
      <p className="dim">
        Read-only pulls from connected integrations. Credentials are set via environment variables on the
        server — no credentials are stored in the dashboard.
      </p>

      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
        {SOURCES.map(s => (
          <button
            key={s.key}
            className={`btn ${active === s.key ? "" : "btn-secondary"}`}
            onClick={() => setActive(s.key)}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
          <div>
            <strong>{src.label}</strong>
            <p className="dim" style={{ margin: "0.25rem 0 0" }}>{src.note}</p>
          </div>
          <button
            className="btn"
            onClick={() => pull(active)}
            disabled={loading === active}
          >
            {loading === active ? "Pulling…" : "Pull Now"}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          {error.includes("409")
            ? "Credentials not configured on the server. Set the required environment variables and restart the API."
            : error}
        </div>
      )}

      {result && !error && (
        <div>
          <div style={{ display: "flex", gap: "1.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
            <div className="card" style={{ flex: "1", minWidth: "120px", textAlign: "center" }}>
              <div style={{ fontSize: "1.75rem", fontWeight: 700 }}>{result.total_rows}</div>
              <div className="dim">Total rows</div>
            </div>
            <div className="card" style={{ flex: "1", minWidth: "120px", textAlign: "center" }}>
              <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--green)" }}>{result.ok_count}</div>
              <div className="dim">OK</div>
            </div>
            <div className="card" style={{ flex: "1", minWidth: "120px", textAlign: "center" }}>
              <div style={{ fontSize: "1.75rem", fontWeight: 700, color: result.review_count > 0 ? "var(--yellow)" : undefined }}>{result.review_count}</div>
              <div className="dim">Review</div>
            </div>
          </div>
          <ResultTable result={result} />
        </div>
      )}

      {!result && !error && !loading && (
        <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
          <p className="dim">Click <strong>Pull Now</strong> to fetch live data from {src.label}.</p>
        </div>
      )}
    </div>
  );
}
