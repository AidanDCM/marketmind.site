import { useEffect, useState } from "react";
import {
  ImportBatch,
  ImportResult,
  listImportHistory,
  pullAndSaveShopifyOrders,
  pullAndSaveShopifyProducts,
  pullAndSaveStripeOrders,
  fetchOrderLifecycle,
  importAdCsv,
  fetchAdSpendSummary,
  type OrderLifecycleEntry,
  type AdSpendSummary,
} from "../api/client";

type SourceKey = "stripe_orders" | "shopify_orders" | "shopify_products";

const SOURCES: { key: SourceKey; label: string; note: string }[] = [
  { key: "stripe_orders", label: "Stripe Charges", note: "Requires STRIPE_API_KEY on the server" },
  { key: "shopify_orders", label: "Shopify Orders", note: "Requires SHOPIFY_STORE_DOMAIN + SHOPIFY_ACCESS_TOKEN" },
  { key: "shopify_products", label: "Shopify Products", note: "Requires SHOPIFY_STORE_DOMAIN + SHOPIFY_ACCESS_TOKEN" },
];

const SOURCE_NAMES: Record<SourceKey, string> = {
  stripe_orders: "stripe_charges",
  shopify_orders: "shopify_orders",
  shopify_products: "shopify_products",
};

function doPull(key: SourceKey): Promise<ImportResult & { batch_id: number }> {
  if (key === "stripe_orders") return pullAndSaveStripeOrders();
  if (key === "shopify_orders") return pullAndSaveShopifyOrders();
  return pullAndSaveShopifyProducts();
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
  const [history, setHistory] = useState<ImportBatch[]>([]);
  const [orders, setOrders] = useState<OrderLifecycleEntry[]>([]);
  const [adCsv, setAdCsv] = useState("");
  const [adResult, setAdResult] = useState<(ImportResult & { batch_id: number }) | null>(null);
  const [adError, setAdError] = useState<string | null>(null);
  const [adLoading, setAdLoading] = useState(false);
  const [adSummary, setAdSummary] = useState<AdSpendSummary | null>(null);

  useEffect(() => {
    listImportHistory().then(setHistory).catch(() => {});
    fetchOrderLifecycle().then(r => setOrders(r.orders)).catch(() => {});
    fetchAdSpendSummary().then(r => { if (r.has_data && r.summary) setAdSummary(r.summary); }).catch(() => {});
  }, [results, adResult]);

  async function pull(key: SourceKey) {
    setLoading(key);
    setErrors(e => ({ ...e, [key]: undefined }));
    try {
      const data = await doPull(key);
      setResults(r => ({ ...r, [key]: data }));
    } catch (err) {
      setErrors(e => ({ ...e, [key]: (err as Error).message }));
    } finally {
      setLoading(null);
    }
  }

  async function submitAdCsv() {
    setAdLoading(true);
    setAdError(null);
    try {
      const data = await importAdCsv(adCsv);
      setAdResult(data);
    } catch (err) {
      setAdError((err as Error).message);
    } finally {
      setAdLoading(false);
    }
  }

  const src = SOURCES.find(s => s.key === active)!;
  const result = results[active];
  const error = errors[active];
  const activeHistory = history.filter(b => b.source === SOURCE_NAMES[active]);

  return (
    <div>
      <h2>Live Data Sources</h2>
      <p className="dim">
        Read-only pulls from connected integrations. Credentials are set via environment variables on the
        server — no credentials are stored in the dashboard.
      </p>

      {orders.length > 0 && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <div className="card-title">Order lifecycle ({orders.length})</div>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr><th>Order</th><th>Stage</th><th>Source</th><th>Amount</th></tr>
              </thead>
              <tbody>
                {orders.slice(0, 10).map(o => (
                  <tr key={`${o.source}-${o.order_id}`}>
                    <td><code>{o.order_id}</code></td>
                    <td>{o.stage}</td>
                    <td>{o.source}</td>
                    <td>{o.amount} {o.currency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-title">Ad performance CSV</div>
        <p className="dim" style={{ marginTop: 0 }}>
          Paste a Meta, Google, or TikTok ad export (campaign, spend, clicks, etc.). No live API required.
        </p>
        {adSummary && (
          <div className="metric-grid" style={{ marginBottom: 12 }}>
            <div className="metric-card">
              <div className="metric-label">Total spend</div>
              <div className="metric-value">${adSummary.total_spend.toFixed(2)}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Campaigns</div>
              <div className="metric-value">{adSummary.campaigns}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Purchases</div>
              <div className="metric-value">{adSummary.total_purchases}</div>
            </div>
          </div>
        )}
        <textarea
          value={adCsv}
          onChange={e => setAdCsv(e.target.value)}
          placeholder={"campaign_name,date,impressions,clicks,spend,purchases,revenue\nMy Campaign,2026-06-15,1000,50,25.00,3,177.00"}
          rows={5}
          style={{ width: "100%", fontFamily: "monospace", fontSize: 12 }}
        />
        <button className="btn" style={{ marginTop: 10 }} onClick={submitAdCsv} disabled={adLoading || !adCsv.trim()}>
          {adLoading ? "Importing…" : "Import CSV"}
        </button>
        {adError && <div className="error-banner" style={{ marginTop: 10 }}>{adError}</div>}
        {adResult && !adError && (
          <p className="dim" style={{ marginTop: 10 }}>
            Batch #{adResult.batch_id}: {adResult.ok_count} OK, {adResult.review_count} review
          </p>
        )}
      </div>

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

      {activeHistory.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h3 style={{ fontSize: "13px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
            Pull History — {src.label}
          </h3>
          <div className="card" style={{ padding: 0, overflow: "hidden" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Pulled at</th>
                  <th>Total</th>
                  <th>OK</th>
                  <th>Review</th>
                </tr>
              </thead>
              <tbody>
                {activeHistory.map(b => (
                  <tr key={b.id}>
                    <td>{new Date(b.pulled_at).toLocaleString()}</td>
                    <td>{b.total_rows}</td>
                    <td style={{ color: "var(--green)" }}>{b.ok_count}</td>
                    <td style={{ color: b.review_count > 0 ? "var(--yellow)" : undefined }}>{b.review_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
