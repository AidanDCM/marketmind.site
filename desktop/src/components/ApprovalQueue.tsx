import { useEffect, useState } from "react";
import {
  fetchApprovals,
  approveRecord,
  denyRecord,
  type ApprovalRecord,
} from "../api/client";

const FILTERS = ["pending", "all", "approved", "denied", "blocked", "auto_allowed"] as const;

function statusBadge(s: string) {
  const map: Record<string, string> = {
    pending: "badge-pending",
    approved: "badge-approved",
    denied: "badge-denied",
    blocked: "badge-blocked",
    auto_allowed: "badge-auto",
    expired: "badge-pending",
  };
  return `badge ${map[s] ?? "badge-pending"}`;
}

function riskBadge(r: string) {
  const map: Record<string, string> = {
    low: "badge-low",
    medium: "badge-medium",
    high: "badge-high",
    critical: "badge-critical",
  };
  return `badge ${map[r.toLowerCase()] ?? "badge-medium"}`;
}

function Card({ rec, onAction }: { rec: ApprovalRecord; onAction: () => void }) {
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const canAct = rec.status === "pending";

  async function act(fn: typeof approveRecord) {
    setBusy(true); setErr(null);
    try { await fn(rec.approval_id, note); onAction(); }
    catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }

  return (
    <div className="approval-card">
      <div className="approval-header" onClick={() => setOpen(o => !o)}>
        <div>
          <div className="approval-title">{rec.summary}</div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 3 }}>{rec.action}</div>
        </div>
        <div className="approval-meta">
          <span className={riskBadge(rec.risk_level)}>{rec.risk_level}</span>
          <span className={statusBadge(rec.status)}>{rec.status}</span>
          {rec.expected_cost > 0 && (
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              ${rec.expected_cost.toFixed(2)}
            </span>
          )}
          <svg className={`chevron ${open ? "open" : ""}`} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>

      {open && (
        <div className="approval-body">
          <div className="approval-detail">
            <div>
              <div className="detail-label">Action</div>
              <div className="detail-value">{rec.action}</div>
            </div>
            <div>
              <div className="detail-label">Expected Cost</div>
              <div className="detail-value">${rec.expected_cost.toFixed(2)}</div>
            </div>
            {rec.rollback_plan && (
              <div style={{ gridColumn: "1 / -1" }}>
                <div className="detail-label">Rollback Plan</div>
                <div className="detail-value">{rec.rollback_plan}</div>
              </div>
            )}
            {rec.reason && (
              <div style={{ gridColumn: "1 / -1" }}>
                <div className="detail-label">Gate Reason</div>
                <div className="detail-value">{rec.reason}</div>
              </div>
            )}
          </div>

          {canAct && (
            <>
              {err && <div className="alert alert-error" style={{ marginBottom: 10 }}>{err}</div>}
              <div className="note-row" style={{ marginBottom: 10 }}>
                <input
                  type="text"
                  placeholder="Optional note..."
                  value={note}
                  onChange={e => setNote(e.target.value)}
                />
              </div>
              <div className="approval-actions">
                <button className="btn-success" disabled={busy} onClick={() => act(approveRecord)}>
                  {busy ? "…" : "Approve"}
                </button>
                <button className="btn-danger" disabled={busy} onClick={() => act(denyRecord)}>
                  {busy ? "…" : "Deny"}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export function ApprovalQueue() {
  const [filter, setFilter] = useState<string>("pending");
  const [records, setRecords] = useState<ApprovalRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true); setError(null);
    const statusArg = filter === "all" ? undefined : filter;
    fetchApprovals(statusArg)
      .then(setRecords)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [filter]);

  return (
    <div className="page">
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2>Approval Queue</h2>
          <p>Review and act on pending operator actions</p>
        </div>
        <button className="btn-ghost" onClick={load}>↺ Refresh</button>
      </div>

      <div className="filter-bar">
        {FILTERS.map(f => (
          <button key={f} className={`filter-btn ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
            {f.replace("_", " ")}
          </button>
        ))}
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <div className="loading-row"><div className="spinner" /></div>}

      {!loading && records.length === 0 && !error && (
        <div className="empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
          <p>No {filter === "all" ? "" : filter} approvals</p>
        </div>
      )}

      <div className="approval-list">
        {records.map(r => (
          <Card key={r.approval_id} rec={r} onAction={load} />
        ))}
      </div>
    </div>
  );
}
