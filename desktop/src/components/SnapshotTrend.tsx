import { useCallback, useEffect, useState } from "react";
import { getSnapshotTrend, type SnapshotRecord } from "../api/client";

const DAY_OPTIONS = [7, 14, 30, 60, 90];

// ---- tiny SVG line chart ----

interface Point { x: number; y: number }

function polyline(pts: Point[]): string {
  return pts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
}

function LineChart({ rows }: { rows: SnapshotRecord[] }) {
  if (rows.length === 0) return <p className="dim">No data to chart.</p>;

  const W = 560, H = 200, PAD = { top: 16, right: 16, bottom: 32, left: 56 };
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;

  const cacs = rows.map(r => r.actual_cac);
  const bep = rows[0].break_even_cac;
  const allVals = [...cacs, bep, 0];
  const minY = Math.min(...allVals) * 0.9;
  const maxY = Math.max(...allVals) * 1.1 || 1;

  function sx(i: number) { return PAD.left + (i / Math.max(rows.length - 1, 1)) * innerW; }
  function sy(v: number) { return PAD.top + innerH - ((v - minY) / (maxY - minY)) * innerH; }

  const cacPts = rows.map((r, i) => ({ x: sx(i), y: sy(r.actual_cac) }));
  const revPts = rows.map((r, i) => ({ x: sx(i), y: sy(r.total_revenue / Math.max(r.orders, 1)) }));
  const bepY = sy(bep);

  const labels = rows.map(r => r.snapshot_date.slice(5)); // MM-DD

  const yTicks = 4;
  const yStep = (maxY - minY) / yTicks;

  return (
    <div style={{ overflowX: "auto" }}>
      <svg width={W} height={H} style={{ fontFamily: "inherit", display: "block" }}>
        {/* grid lines */}
        {Array.from({ length: yTicks + 1 }, (_, i) => {
          const v = minY + i * yStep;
          const y = sy(v);
          return (
            <g key={i}>
              <line x1={PAD.left} y1={y} x2={W - PAD.right} y2={y} stroke="var(--border)" strokeWidth={0.5} />
              <text x={PAD.left - 6} y={y + 4} textAnchor="end" fontSize={10} fill="var(--text-muted)">
                ${v.toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* break-even reference line */}
        <line x1={PAD.left} y1={bepY} x2={W - PAD.right} y2={bepY}
          stroke="var(--yellow, #f5a623)" strokeWidth={1.5} strokeDasharray="4 3" />
        <text x={W - PAD.right + 4} y={bepY + 4} fontSize={9} fill="var(--yellow, #f5a623)">BEP</text>

        {/* CAC line */}
        {cacPts.length > 1 && (
          <polyline points={polyline(cacPts)} fill="none" stroke="var(--accent, #6366f1)" strokeWidth={2} strokeLinejoin="round" />
        )}
        {cacPts.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={3} fill="var(--accent, #6366f1)" />
        ))}

        {/* Revenue/order line (avg order value) */}
        {revPts.length > 1 && (
          <polyline points={polyline(revPts)} fill="none" stroke="var(--green, #22c55e)" strokeWidth={1.5}
            strokeLinejoin="round" strokeDasharray="6 2" />
        )}

        {/* x-axis labels */}
        {rows.map((_, i) => {
          const x = sx(i);
          const show = rows.length <= 10 || i % Math.ceil(rows.length / 8) === 0 || i === rows.length - 1;
          return show ? (
            <text key={i} x={x} y={H - 6} textAnchor="middle" fontSize={9} fill="var(--text-muted)">
              {labels[i]}
            </text>
          ) : null;
        })}
      </svg>

      {/* legend */}
      <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.5rem", fontSize: 12, color: "var(--text-muted)" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <svg width="20" height="4"><line x1="0" y1="2" x2="20" y2="2" stroke="var(--accent, #6366f1)" strokeWidth="2"/></svg>
          Actual CAC
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <svg width="20" height="4"><line x1="0" y1="2" x2="20" y2="2" stroke="var(--yellow, #f5a623)" strokeWidth="2" strokeDasharray="4 3"/></svg>
          Break-even CAC
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <svg width="20" height="4"><line x1="0" y1="2" x2="20" y2="2" stroke="var(--green, #22c55e)" strokeWidth="2" strokeDasharray="6 2"/></svg>
          Avg order value
        </span>
      </div>
    </div>
  );
}

function MetricsTable({ rows }: { rows: SnapshotRecord[] }) {
  return (
    <div style={{ overflowX: "auto", marginTop: "1rem" }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Orders</th>
            <th>Revenue</th>
            <th>Ad Spend</th>
            <th>CAC</th>
            <th>Conv%</th>
            <th>Refund%</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{r.snapshot_date}</td>
              <td>{r.orders}</td>
              <td>${r.total_revenue.toFixed(2)}</td>
              <td>${r.total_ad_spend.toFixed(2)}</td>
              <td style={{ color: r.actual_cac > r.break_even_cac ? "var(--red)" : "var(--green)" }}>
                ${r.actual_cac.toFixed(2)}
              </td>
              <td>{(r.conversion_rate * 100).toFixed(1)}%</td>
              <td>{(r.refund_rate * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SnapshotTrend({
  initialExperimentId = null,
  initialDays = null,
}: {
  initialExperimentId?: string | null;
  initialDays?: number | null;
} = {}) {
  const [experimentId, setExperimentId] = useState(initialExperimentId ?? "");
  const [days, setDays] = useState(initialDays ?? 30);
  const [rows, setRows] = useState<SnapshotRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queried, setQueried] = useState(false);

  const loadWithParams = useCallback((id: string, lookback: number) => {
    if (!id) return;
    setLoading(true);
    setError(null);
    setQueried(true);
    getSnapshotTrend(id, lookback)
      .then(setRows)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  function load(id = experimentId.trim(), lookback = days) {
    loadWithParams(id, lookback);
  }

  useEffect(() => {
    const id = initialExperimentId?.trim();
    if (!id) return;
    const lookback = initialDays ?? 30;
    setExperimentId(id);
    setDays(lookback);
    loadWithParams(id, lookback);
  }, [initialExperimentId, initialDays, loadWithParams]);

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter") load();
  }

  const totalOrders = rows.reduce((s, r) => s + r.orders, 0);
  const totalRevenue = rows.reduce((s, r) => s + r.total_revenue, 0);
  const totalSpend = rows.reduce((s, r) => s + r.total_ad_spend, 0);
  const avgCac = totalOrders > 0 ? totalSpend / totalOrders : 0;
  const bep = rows[0]?.break_even_cac ?? 0;

  return (
    <div>
      <h2>Experiment Trend</h2>
      <p className="dim">CAC vs break-even over time for a live experiment.</p>

      <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.25rem", alignItems: "flex-end" }}>
        <label style={{ flex: 1, fontSize: 12, color: "var(--text-muted)" }}>
          Experiment ID
          <input
            className="input"
            style={{ marginTop: 4, width: "100%" }}
            placeholder="exp_interior_kit_001"
            value={experimentId}
            onChange={e => setExperimentId(e.target.value)}
            onKeyDown={handleKey}
          />
        </label>
        <label style={{ fontSize: 12, color: "var(--text-muted)" }}>
          Days back
          <select
            className="input"
            style={{ marginTop: 4, display: "block" }}
            value={days}
            onChange={e => setDays(Number(e.target.value))}
          >
            {DAY_OPTIONS.map(d => <option key={d} value={d}>{d} days</option>)}
          </select>
        </label>
        <button className="btn" onClick={() => load()} disabled={loading || !experimentId.trim()}>
          {loading ? "Loading…" : "Load"}
        </button>
      </div>

      {error && <div className="error-banner" style={{ marginTop: "1rem" }}>{error}</div>}

      {queried && !loading && !error && rows.length === 0 && (
        <p className="dim" style={{ marginTop: "1rem" }}>No snapshots found for <code>{experimentId}</code> in the last {days} days.</p>
      )}

      {rows.length > 0 && (
        <>
          {/* summary stats */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.75rem", margin: "1.25rem 0" }}>
            {[
              ["Total Orders", totalOrders.toString()],
              ["Total Revenue", `$${totalRevenue.toFixed(2)}`],
              ["Total Spend", `$${totalSpend.toFixed(2)}`],
              ["Avg CAC", `$${avgCac.toFixed(2)}`],
            ].map(([label, val]) => (
              <div className="card" key={label} style={{ padding: "0.75rem" }}>
                <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</div>
                <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4,
                  color: label === "Avg CAC" ? (avgCac > bep ? "var(--red)" : "var(--green)") : "var(--text)" }}>
                  {val}
                </div>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-title">CAC over time ({rows.length} days recorded)</div>
            <LineChart rows={rows} />
          </div>

          <div className="card" style={{ marginTop: "1rem" }}>
            <div className="card-title">Daily breakdown</div>
            <MetricsTable rows={rows} />
          </div>
        </>
      )}
    </div>
  );
}
