import { useEffect, useState } from "react";
import { listSnapshots, SnapshotRecord, SnapshotRequest, submitSnapshot } from "../api/client";

const TODAY = new Date().toISOString().slice(0, 10);

const DEFAULTS: SnapshotRequest = {
  experiment_id: "",
  product_name: "",
  break_even_cac: 25,
  snapshot_date: TODAY,
  qualified_visits: 0,
  orders: 0,
  total_ad_spend: 0,
  total_revenue: 0,
  refund_count: 0,
  actual_shipping_cost: 0,
  planned_shipping_cost: 0,
  add_to_cart_count: 0,
  consecutive_losing_periods: 0,
  budget_cap: 500,
};

function num(v: string): number { return parseFloat(v) || 0; }
function int(v: string): number { return parseInt(v, 10) || 0; }

function pct(n: number) { return `${(n * 100).toFixed(1)}%`; }

function SnapshotTable({ snapshots }: { snapshots: SnapshotRecord[] }) {
  if (snapshots.length === 0) return <p className="dim">No snapshots for this date.</p>;
  return (
    <div style={{ overflowX: "auto" }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>Experiment</th>
            <th>Product</th>
            <th>Visits</th>
            <th>Orders</th>
            <th>Conv%</th>
            <th>Revenue</th>
            <th>Ad Spend</th>
            <th>CAC</th>
            <th>BEP CAC</th>
          </tr>
        </thead>
        <tbody>
          {snapshots.map((s, i) => (
            <tr key={i}>
              <td><code>{s.experiment_id}</code></td>
              <td>{s.product_name}</td>
              <td>{s.qualified_visits}</td>
              <td>{s.orders}</td>
              <td>{pct(s.conversion_rate)}</td>
              <td>${s.total_revenue.toFixed(2)}</td>
              <td>${s.total_ad_spend.toFixed(2)}</td>
              <td style={{ color: s.actual_cac > s.break_even_cac ? "var(--red)" : "var(--green)" }}>
                ${s.actual_cac.toFixed(2)}
              </td>
              <td className="dim">${s.break_even_cac.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SnapshotRecorder() {
  const [form, setForm] = useState<SnapshotRequest>(DEFAULTS);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [snapshots, setSnapshots] = useState<SnapshotRecord[]>([]);
  const [listDate, setListDate] = useState(TODAY);
  const [listLoading, setListLoading] = useState(false);

  function set(field: keyof SnapshotRequest, value: string | number) {
    setForm(f => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSuccess(null);
    if (!form.experiment_id.trim()) { setFormError("Experiment ID is required"); return; }
    if (!form.product_name.trim()) { setFormError("Product name is required"); return; }
    setSubmitting(true);
    try {
      await submitSnapshot(form);
      setSuccess(`Snapshot recorded for ${form.experiment_id} on ${form.snapshot_date || TODAY}.`);
      loadSnapshots(form.snapshot_date || TODAY);
    } catch (err) {
      setFormError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  function loadSnapshots(d: string) {
    setListLoading(true);
    listSnapshots(d).then(setSnapshots).catch(() => {}).finally(() => setListLoading(false));
  }

  useEffect(() => { loadSnapshots(listDate); }, [listDate]);

  return (
    <div>
      <h2>Snapshot Recorder</h2>
      <p className="dim">Submit observed performance data for a live experiment. The daily cycle picks these up automatically.</p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", marginTop: "1.5rem" }}>
        {/* Form */}
        <div>
          <form onSubmit={handleSubmit}>
            <div className="card">
              <div className="card-title">Experiment</div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <label style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Experiment ID
                  <input className="input" value={form.experiment_id} onChange={e => set("experiment_id", e.target.value)} placeholder="exp_interior_kit_001" style={{ marginTop: "4px", width: "100%" }} />
                </label>
                <label style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Product name
                  <input className="input" value={form.product_name} onChange={e => set("product_name", e.target.value)} placeholder="Interior Kit" style={{ marginTop: "4px", width: "100%" }} />
                </label>
                <label style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Break-even CAC ($)
                  <input className="input" type="number" step="0.01" value={form.break_even_cac} onChange={e => set("break_even_cac", num(e.target.value))} style={{ marginTop: "4px", width: "100%" }} />
                </label>
                <label style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Snapshot date
                  <input className="input" type="date" value={form.snapshot_date || TODAY} onChange={e => set("snapshot_date", e.target.value)} style={{ marginTop: "4px", width: "100%" }} />
                </label>
              </div>
            </div>

            <div className="card" style={{ marginTop: "1rem" }}>
              <div className="card-title">Performance counters</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                {([
                  ["qualified_visits", "Qualified visits", "int"],
                  ["orders", "Orders", "int"],
                  ["total_ad_spend", "Ad spend ($)", "num"],
                  ["total_revenue", "Revenue ($)", "num"],
                  ["add_to_cart_count", "Add-to-cart", "int"],
                  ["refund_count", "Refund count", "int"],
                  ["actual_shipping_cost", "Actual shipping ($)", "num"],
                  ["planned_shipping_cost", "Planned shipping ($)", "num"],
                  ["consecutive_losing_periods", "Consecutive losing periods", "int"],
                  ["budget_cap", "Budget cap ($)", "num"],
                ] as [keyof SnapshotRequest, string, string][]).map(([f, lbl, typ]) => (
                  <label key={f} style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                    {lbl}
                    <input
                      className="input"
                      type="number"
                      step={typ === "num" ? "0.01" : "1"}
                      value={form[f] as number}
                      onChange={e => set(f, typ === "int" ? int(e.target.value) : num(e.target.value))}
                      style={{ marginTop: "4px", width: "100%" }}
                    />
                  </label>
                ))}
              </div>
            </div>

            {formError && <div className="error-banner" style={{ marginTop: "1rem" }}>{formError}</div>}
            {success && <div className="alert alert-warn" style={{ marginTop: "1rem" }}>{success}</div>}

            <button className="btn" type="submit" style={{ marginTop: "1rem", width: "100%" }} disabled={submitting}>
              {submitting ? "Recording…" : "Record Snapshot"}
            </button>
          </form>
        </div>

        {/* List */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <h3 style={{ margin: 0, fontSize: "14px" }}>Recorded snapshots</h3>
            <input type="date" value={listDate} onChange={e => setListDate(e.target.value)} className="input" style={{ fontSize: "13px", padding: "4px 8px" }} />
          </div>
          {listLoading ? <p className="dim">Loading…</p> : <SnapshotTable snapshots={snapshots} />}
        </div>
      </div>
    </div>
  );
}
