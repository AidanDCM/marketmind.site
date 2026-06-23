import { useEffect, useState } from "react";
import {
  fetchDailyReport,
  fetchPendingApprovals,
  fetchOperatorPreflight,
  fetchExperimentPortfolio,
  fetchAdSpendSummary,
  fetchOperatorIntegrations,
  type DailyReport,
  type ApprovalRecord,
  type OperatorPreflight,
  type ExperimentPortfolio,
  type AdSpendSummary,
  type OperatorIntegrations,
} from "../api/client";

function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

function fmt$(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function fmtPct(n: number): string {
  return (n * 100).toFixed(1) + "%";
}

export function Overview() {
  const [date, setDate] = useState(todayStr());
  const [report, setReport] = useState<DailyReport | null>(null);
  const [pending, setPending] = useState<ApprovalRecord[]>([]);
  const [preflight, setPreflight] = useState<OperatorPreflight | null>(null);
  const [portfolio, setPortfolio] = useState<ExperimentPortfolio | null>(null);
  const [adSpend, setAdSpend] = useState<AdSpendSummary | null>(null);
  const [integrations, setIntegrations] = useState<OperatorIntegrations | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      fetchDailyReport(date),
      fetchPendingApprovals(),
      fetchOperatorPreflight(),
      fetchExperimentPortfolio(),
      fetchAdSpendSummary(),
      fetchOperatorIntegrations(),
    ])
      .then(([r, p, pf, port, ads, integ]) => {
        if (!cancelled) {
          setReport(r);
          setPending(p);
          setPreflight(pf);
          setPortfolio(port);
          setAdSpend(ads.has_data && ads.summary ? ads.summary : null);
          setIntegrations(integ);
        }
      })
      .catch((e: Error) => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [date]);

  const m = report?.metrics;

  return (
    <div className="page">
      <div className="page-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h2>Overview</h2>
          <p>Daily performance metrics and operator alerts</p>
        </div>
        <input type="date" value={date} max={todayStr()} onChange={(e) => setDate(e.target.value)} style={{ width: 160 }} />
      </div>

      {portfolio && (
        <div className="metric-grid" style={{ marginBottom: 14 }}>
          <div className="metric-card">
            <div className="metric-label">Experiments</div>
            <div className="metric-value">{portfolio.total_experiments}</div>
            <div className="metric-sub">{portfolio.active} active · {portfolio.ended} ended</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Need attention</div>
            <div className={`metric-value ${portfolio.needs_attention > 0 ? "metric-down" : "metric-up"}`}>
              {portfolio.needs_attention}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Lessons recorded</div>
            <div className="metric-value">{portfolio.lessons_recorded}</div>
          </div>
        </div>
      )}

      {adSpend && (
        <div className="metric-grid" style={{ marginBottom: 14 }}>
          <div className="metric-card">
            <div className="metric-label">Imported ad spend</div>
            <div className="metric-value">{fmt$(adSpend.total_spend)}</div>
            <div className="metric-sub">{adSpend.campaigns} campaigns (latest CSV batch)</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Ad clicks</div>
            <div className="metric-value">{adSpend.total_clicks.toLocaleString()}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Ad-attributed revenue</div>
            <div className="metric-value">{fmt$(adSpend.total_revenue)}</div>
            <div className="metric-sub">{adSpend.total_purchases} purchases</div>
          </div>
        </div>
      )}

      {integrations && (
        <p className="dim" style={{ marginBottom: 14, fontSize: 13 }}>
          Gmail: <code>{integrations.gmail.mode}</code>
          {integrations.scheduler.prune_on_cycle && (
            <> · Scheduler prune: {integrations.scheduler.prune_apply ? "apply" : "preview"}</>
          )}
        </p>
      )}

      {preflight && (
        <div className={`alert ${preflight.safe_to_operate ? "alert-ok" : "alert-warn"}`} style={{ marginBottom: 14 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {preflight.safe_to_operate
              ? <><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></>
              : <><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></>
            }
          </svg>
          <div>
            <div style={{ fontWeight: 600 }}>{preflight.summary}</div>
            {preflight.blockers.length > 0 && (
              <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 13 }}>
                {preflight.blockers.map((b, i) => <li key={i}>{b}</li>)}
              </ul>
            )}
            {preflight.experiments_needing_attention.length > 0 && (
              <div style={{ marginTop: 8, fontSize: 12 }}>
                {preflight.experiments_needing_attention.map(e => (
                  <div key={e.experiment_id}>
                    <code>{e.experiment_id}</code> — {e.ruling.replace(/_/g, " ")}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {pending.length > 0 && (
        <div className="alert alert-warn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          {pending.length} pending approval{pending.length !== 1 ? "s" : ""} require your review.
        </div>
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
        </div>
      )}
    </div>
  );
}
