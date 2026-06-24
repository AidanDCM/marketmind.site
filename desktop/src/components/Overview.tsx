import { useEffect, useState } from "react";
import {
  fetchDailyReport,
  fetchPendingApprovals,
  fetchOperatorHealthPanel,
  fetchOperatorReadiness,
  fetchExperimentTrendSummary,
  runOperatorDailyCycle,
  type DailyReport,
  type ApprovalRecord,
  type OperatorHealthPanel,
  type OperatorReadiness,
  type ExperimentTrendSummary,
} from "../api/client";
import { pendingApprovalBannerText } from "../approvalDisplay";
import { runOverviewDailyCycle } from "../overviewDailyCycle";
import { OperatorHealthPanelView } from "./OperatorHealthPanel";
import { OperatorReadinessBanner } from "./OperatorReadinessBanner";
import { RulingBadge } from "./RulingBadge";
import {
  ATTENTION_ONLY_KEY,
  TREND_DAYS_KEY,
  OVERVIEW_DATE_KEY,
  TREND_DAY_OPTIONS,
  readAttentionOnlyPreference,
  readOverviewDatePreference,
  readTrendDaysPreference,
  isSnapshotStale,
  type TrendDayOption,
} from "./overviewPreferences";

function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

function fmt$(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function fmtPct(n: number): string {
  return (n * 100).toFixed(1) + "%";
}

function trendArrow(direction: ExperimentTrendSummary["experiments"][number]["cac_direction"]): string {
  if (direction === "up") return "↑";
  if (direction === "down") return "↓";
  if (direction === "flat") return "→";
  return "·";
}

export function Overview({
  onOpenTrend,
  onOpenActive,
  onOpenApprovals,
  onOpenAttention,
  onOpenSnapshots,
  dataRevision = 0,
  onCycleComplete,
}: {
  onOpenTrend: (experimentId: string, trendDays: number) => void;
  onOpenActive: (experimentId: string) => void;
  onOpenApprovals: (focusApprovalId?: string) => void;
  onOpenAttention: () => void;
  onOpenSnapshots: (snapshotDate: string, experimentId?: string) => void;
  dataRevision?: number;
  onCycleComplete?: () => void;
}) {
  const [date, setDate] = useState(readOverviewDatePreference);
  const [report, setReport] = useState<DailyReport | null>(null);
  const [pending, setPending] = useState<ApprovalRecord[]>([]);
  const [health, setHealth] = useState<OperatorHealthPanel | null>(null);
  const [readiness, setReadiness] = useState<OperatorReadiness | null>(null);
  const [trendSummary, setTrendSummary] = useState<ExperimentTrendSummary | null>(null);
  const [attentionOnly, setAttentionOnly] = useState(readAttentionOnlyPreference);
  const [trendDays, setTrendDays] = useState<TrendDayOption>(readTrendDaysPreference);
  const [loading, setLoading] = useState(false);
  const [cycleRunning, setCycleRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      fetchDailyReport(date),
      fetchPendingApprovals(),
      fetchOperatorHealthPanel(date),
      fetchOperatorReadiness(date),
      fetchExperimentTrendSummary(trendDays, date, attentionOnly),
    ])
      .then(([r, p, h, ready, trends]) => {
        if (!cancelled) {
          setReport(r);
          setPending(p);
          setHealth(h);
          setReadiness(ready);
          setTrendSummary(trends);
        }
      })
      .catch((e: Error) => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [date, attentionOnly, trendDays, dataRevision]);

  useEffect(() => {
    try {
      localStorage.setItem(ATTENTION_ONLY_KEY, attentionOnly ? "true" : "false");
    } catch {
      // ignore storage errors in non-browser contexts
    }
  }, [attentionOnly]);

  useEffect(() => {
    try {
      localStorage.setItem(TREND_DAYS_KEY, String(trendDays));
    } catch {
      // ignore storage errors in non-browser contexts
    }
  }, [trendDays]);

  useEffect(() => {
    try {
      localStorage.setItem(OVERVIEW_DATE_KEY, date);
    } catch {
      // ignore storage errors in non-browser contexts
    }
  }, [date]);

  const m = report?.metrics;

  async function handleRunCycle() {
    setCycleRunning(true);
    setError(null);
    try {
      const [r, p, h, ready, trends] = await runOverviewDailyCycle({
        date,
        trendDays,
        attentionOnly,
        runCycle: runOperatorDailyCycle,
        fetchOverviewData: async (d, td, att) => Promise.all([
          fetchDailyReport(d),
          fetchPendingApprovals(),
          fetchOperatorHealthPanel(d),
          fetchOperatorReadiness(d),
          fetchExperimentTrendSummary(td, d, att),
        ]),
        onCycleComplete,
      });
      setReport(r);
      setPending(p);
      setHealth(h);
      setReadiness(ready);
      setTrendSummary(trends);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCycleRunning(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h2>Overview</h2>
          <p>Daily performance metrics and operator alerts</p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input type="date" value={date} max={todayStr()} onChange={(e) => setDate(e.target.value)} style={{ width: 160 }} />
          <button type="button" className="btn-ghost" style={{ fontSize: 13, whiteSpace: "nowrap" }} onClick={() => onOpenSnapshots(date)}>
            Snapshots
          </button>
        </div>
      </div>

      {readiness && (
        <OperatorReadinessBanner
          readiness={readiness}
          onOpenApprovals={() => onOpenApprovals(pending[0]?.approval_id)}
          onOpenActive={onOpenActive}
          onOpenSnapshots={onOpenSnapshots}
        />
      )}

      {health && (
        <OperatorHealthPanelView
          health={health}
          onRunCycle={handleRunCycle}
          cycleRunning={cycleRunning}
          onRecordSnapshot={onOpenSnapshots}
          onOpenExperiment={onOpenActive}
          onOpenAttention={onOpenAttention}
        />
      )}

      {trendSummary && (trendSummary.experiments.length > 0 || attentionOnly) && (
        <div className="card" style={{ marginBottom: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 10 }}>
            <div className="card-title" style={{ margin: 0 }}>
              Active experiment CAC trends ({trendSummary.days}d through {trendSummary.as_of})
              {!attentionOnly && trendSummary.needs_attention_count > 0 && (
                <button
                  type="button"
                  className="inline-link inline-link-danger"
                  onClick={onOpenAttention}
                >
                  · {trendSummary.needs_attention_count} need attention
                </button>
              )}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 13, whiteSpace: "nowrap" }}>
              <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                Lookback
                <select
                  value={trendDays}
                  onChange={(e) => setTrendDays(Number(e.target.value) as TrendDayOption)}
                  style={{ fontSize: 13 }}
                >
                  {TREND_DAY_OPTIONS.map((days) => (
                    <option key={days} value={days}>{days}d</option>
                  ))}
                </select>
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <input
                  type="checkbox"
                  checked={attentionOnly}
                  onChange={(e) => setAttentionOnly(e.target.checked)}
                />
                Attention only
              </label>
            </div>
          </div>
          {trendSummary.experiments.length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: 13 }}>
              No active experiments need attention for {trendSummary.as_of}.
            </div>
          ) : (
          <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", color: "var(--text-muted)" }}>
                <th style={{ padding: "4px 8px 4px 0" }}>Experiment</th>
                <th style={{ padding: "4px 8px" }}>Latest CAC</th>
                <th style={{ padding: "4px 8px" }}>BEP</th>
                <th style={{ padding: "4px 8px" }}>Snapshot</th>
                <th style={{ padding: "4px 8px" }}>Trend</th>
                <th style={{ padding: "4px 8px" }}>Ruling</th>
                <th style={{ padding: "4px 0 4px 8px" }}>Open</th>
              </tr>
            </thead>
            <tbody>
              {trendSummary.experiments.map(exp => (
                <tr
                  key={exp.experiment_id}
                  style={exp.needs_attention ? { background: "rgba(239, 68, 68, 0.06)" } : undefined}
                >
                  <td style={{ padding: "6px 8px 6px 0" }}>
                    <code>{exp.experiment_id}</code>
                    <div style={{ color: "var(--text-muted)", fontSize: 12 }}>{exp.product_name}</div>
                  </td>
                  <td style={{
                    padding: "6px 8px",
                    color: exp.above_break_even ? "var(--red, #ef4444)" : undefined,
                    fontWeight: exp.above_break_even ? 600 : undefined,
                  }}>
                    {exp.latest_cac != null ? fmt$(exp.latest_cac) : "—"}
                  </td>
                  <td style={{ padding: "6px 8px" }}>{fmt$(exp.break_even_cac)}</td>
                  <td style={{
                    padding: "6px 8px",
                    color: isSnapshotStale(exp.latest_snapshot_date, trendSummary.as_of)
                      ? "var(--yellow, #f5a623)"
                      : "var(--text-muted)",
                    fontWeight: isSnapshotStale(exp.latest_snapshot_date, trendSummary.as_of) ? 600 : undefined,
                  }}>
                    {exp.latest_snapshot_date ?? "—"}
                    {isSnapshotStale(exp.latest_snapshot_date, trendSummary.as_of) && (
                      <>
                        <span title="No snapshot on selected date"> · stale</span>
                        <button
                          type="button"
                          className="inline-link inline-link-danger"
                          style={{ marginLeft: 6, fontSize: 12 }}
                          onClick={() => onOpenSnapshots(trendSummary.as_of, exp.experiment_id)}
                        >
                          Record
                        </button>
                      </>
                    )}
                  </td>
                  <td style={{ padding: "6px 8px", fontWeight: 600,
                    color: exp.cac_direction === "up" ? "var(--red, #ef4444)"
                      : exp.cac_direction === "down" ? "var(--green, #22c55e)"
                      : "var(--text-muted)" }}>
                    {trendArrow(exp.cac_direction)}
                  </td>
                  <td style={{ padding: "6px 0 6px 8px" }}>
                    <RulingBadge ruling={exp.ruling} />
                  </td>
                  <td style={{ padding: "6px 0 6px 8px", whiteSpace: "nowrap" }}>
                    <button
                      type="button"
                      className="btn-ghost"
                      style={{ fontSize: 12, padding: "2px 8px", marginRight: 4 }}
                      onClick={() => onOpenTrend(exp.experiment_id, trendDays)}
                    >
                      Chart
                    </button>
                    <button
                      type="button"
                      className="btn-ghost"
                      style={{ fontSize: 12, padding: "2px 8px" }}
                      onClick={() => onOpenActive(exp.experiment_id)}
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          )}
        </div>
      )}

      {pending.length > 0 && (
        <button type="button" className="alert alert-warn alert-action" onClick={() => onOpenApprovals(pending[0]?.approval_id)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          {pendingApprovalBannerText(pending)}
        </button>
      )}

      {loading && <div className="loading-row"><div className="spinner" /></div>}
      {error && <div className="alert alert-error">API error: {error}</div>}

      {m && (
        <>
          <div className="metric-grid">
            <div className="metric-card">
              <div className="metric-label">Orders</div>
              <div className="metric-value">{m.orders}</div>
              <div className="metric-sub">for {date}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Revenue</div>
              <div className="metric-value">{fmt$(m.revenue)}</div>
              <div className="metric-sub">gross</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Ad Spend</div>
              <div className="metric-value metric-down">{fmt$(m.ad_spend)}</div>
              <div className="metric-sub">total spend</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">CAC</div>
              <div className="metric-value">{fmt$(m.cac)}</div>
              <div className="metric-sub">per order</div>
            </div>
          </div>

          <div className="metric-grid">
            <div className="metric-card">
              <div className="metric-label">Contribution Profit</div>
              <div className={`metric-value ${m.contribution_profit >= 0 ? "metric-up" : "metric-down"}`}>
                {fmt$(m.contribution_profit)}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Conversion</div>
              <div className="metric-value">{fmtPct(m.conversion_rate)}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Add-to-Cart</div>
              <div className="metric-value">{fmtPct(m.add_to_cart_rate)}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Refund Rate</div>
              <div className={`metric-value ${m.refund_rate < 0.05 ? "metric-up" : "metric-down"}`}>
                {fmtPct(m.refund_rate)}
              </div>
            </div>
          </div>

          <div className="two-col">
            <div className="card">
              <div className="card-title">Risks</div>
              {report!.risks.length === 0
                ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No risks flagged</div>
                : report!.risks.map((r, i) => (
                  <div key={i} className="list-item"><div className="bullet risk" /><div className="list-text">{r}</div></div>
                ))}
            </div>
            <div className="card">
              <div className="card-title">Recommendations</div>
              {report!.recommendations.length === 0
                ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No recommendations</div>
                : report!.recommendations.map((r, i) => (
                  <div key={i} className="list-item"><div className="bullet rec" /><div className="list-text">{r}</div></div>
                ))}
            </div>
          </div>

          {report!.lessons.length > 0 && (
            <div className="card" style={{ marginTop: 14 }}>
              <div className="card-title">Lessons</div>
              {report!.lessons.map((l, i) => (
                <div key={i} className="list-item"><div className="bullet" style={{ background: "var(--accent)" }} /><div className="list-text">{l}</div></div>
              ))}
            </div>
          )}
        </>
      )}

      {!loading && !m && !error && (
        <div className="empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="12" y2="17"/></svg>
          <p>No report data for {date}</p>
          <button type="button" className="btn-ghost" style={{ marginTop: 8 }} onClick={() => onOpenSnapshots(date)}>
            Record a snapshot for {date}
          </button>
        </div>
      )}
    </div>
  );
}
