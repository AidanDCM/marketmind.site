import type {
  OperatorPreflight,
  OperatorIntegrations,
  ExperimentPortfolio,
  AdSpendSummary,
} from "../api/client";

export interface OperatorHealthPanel {
  safe_to_operate: boolean;
  warnings: string[];
  preflight: OperatorPreflight;
  integrations: OperatorIntegrations;
  portfolio: ExperimentPortfolio;
  ad_spend: { has_data: boolean; summary: AdSpendSummary | null };
  checklist: { min_visits: number; min_orders: number; min_spend: number };
  last_cycle: {
    event_id: string;
    created_at: string;
    date: string;
    experiments_evaluated: number;
    approvals_created: number;
  } | null;
}

interface OperatorHealthPanelProps {
  health: OperatorHealthPanel;
  onRunCycle?: () => void;
  cycleRunning?: boolean;
}

export function OperatorHealthPanelView({ health, onRunCycle, cycleRunning }: OperatorHealthPanelProps) {
  const { preflight, integrations, portfolio, ad_spend: adSpendBlock } = health;
  const adSpend = adSpendBlock.has_data && adSpendBlock.summary ? adSpendBlock.summary : null;

  return (
    <>
      {health.warnings.length > 0 && (
        <div className="alert alert-warn" style={{ marginBottom: 14 }}>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
            {health.warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

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

      <div className="metric-grid" style={{ marginBottom: 14 }}>
        <div className="metric-card">
          <div className="metric-label">Gmail</div>
          <div className="metric-value" style={{ fontSize: 18 }}>{integrations.gmail.mode}</div>
          <div className="metric-sub">{integrations.gmail.live_ready ? "live-ready" : "not live"}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Stripe</div>
          <div className="metric-value" style={{ fontSize: 18 }}>
            {integrations.stripe.configured ? "configured" : "missing"}
          </div>
          <div className="metric-sub">{integrations.stripe.dry_run ? "dry-run" : "live-ready"}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Shopify</div>
          <div className="metric-value" style={{ fontSize: 18 }}>
            {integrations.shopify.configured ? "configured" : "missing"}
          </div>
          <div className="metric-sub">{integrations.shopify.read_only ? "read-only" : "live-ready"}</div>
        </div>
      </div>

      {health.last_cycle ? (
        <div className="card" style={{ marginBottom: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
            <div>
              <div className="card-title">Last daily cycle</div>
              <p className="dim" style={{ margin: "0 0 8px" }}>
                {health.last_cycle.date} · ran {new Date(health.last_cycle.created_at).toLocaleString()}
              </p>
              <div style={{ fontSize: 13 }}>
                {health.last_cycle.experiments_evaluated} experiment(s) evaluated ·{" "}
                {health.last_cycle.approvals_created} approval(s) queued
              </div>
            </div>
            {onRunCycle && (
              <button className="btn btn-secondary" onClick={onRunCycle} disabled={cycleRunning}>
                {cycleRunning ? "Running…" : "Run cycle now"}
              </button>
            )}
          </div>
        </div>
      ) : onRunCycle && (
        <div className="card" style={{ marginBottom: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div className="card-title">Daily cycle</div>
              <p className="dim" style={{ margin: 0 }}>No cycle recorded yet.</p>
            </div>
            <button className="btn" onClick={onRunCycle} disabled={cycleRunning}>
              {cycleRunning ? "Running…" : "Run cycle now"}
            </button>
          </div>
        </div>
      )}

      {adSpend && (
        <div className="metric-grid" style={{ marginBottom: 14 }}>
          <div className="metric-card">
            <div className="metric-label">Imported ad spend</div>
            <div className="metric-value">
              {adSpend.total_spend.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 })}
            </div>
            <div className="metric-sub">{adSpend.campaigns} campaigns</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Ad clicks</div>
            <div className="metric-value">{adSpend.total_clicks.toLocaleString()}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Ad revenue</div>
            <div className="metric-value">
              {adSpend.total_revenue.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 })}
            </div>
          </div>
        </div>
      )}

      <div className={`alert ${preflight.safe_to_operate ? "alert-ok" : "alert-warn"}`} style={{ marginBottom: 14 }}>
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
    </>
  );
}
