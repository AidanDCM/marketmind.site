import type {
  OperatorPreflight,
  OperatorIntegrations,
  ExperimentPortfolio,
  AdSpendSummary,
} from "../api/client";
import { OperatorMessageListItem } from "./OperatorMessageListItem";

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
  snapshot_gaps: {
    snapshot_date: string;
    active_count: number;
    missing_count: number;
    missing: { experiment_id: string; product_name: string }[];
    all_recorded: boolean;
  };
}

interface OperatorHealthPanelProps {
  health: OperatorHealthPanel;
  onRunCycle?: () => void;
  cycleRunning?: boolean;
  onRecordSnapshot?: (snapshotDate: string, experimentId: string) => void;
  onOpenExperiment?: (experimentId: string) => void;
  onOpenAttention?: () => void;
  onOpenApprovals?: () => void;
  onOpenSnapshots?: (snapshotDate: string, experimentId?: string) => void;
  onOpenActiveList?: () => void;
  onOpenLessons?: () => void;
}

export function OperatorHealthPanelView({
  health,
  onRunCycle,
  cycleRunning,
  onRecordSnapshot,
  onOpenExperiment,
  onOpenAttention,
  onOpenApprovals,
  onOpenSnapshots,
  onOpenActiveList,
  onOpenLessons,
}: OperatorHealthPanelProps) {
  const { preflight, integrations, portfolio, ad_spend: adSpendBlock } = health;
  const adSpend = adSpendBlock.has_data && adSpendBlock.summary ? adSpendBlock.summary : null;
  const messageHandlers = {
    onOpenApprovals,
    onOpenActive: onOpenExperiment,
    onOpenSnapshots,
  };

  return (
    <>
      {health.warnings.length > 0 && (
        <div className="alert alert-warn" style={{ marginBottom: 14 }}>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
            {health.warnings.map((w, i) => (
              <OperatorMessageListItem key={i} text={w} muted {...messageHandlers} />
            ))}
          </ul>
        </div>
      )}

      <div className="metric-grid" style={{ marginBottom: 14 }}>
        <div
          className="metric-card"
          style={onOpenActiveList ? { cursor: "pointer" } : undefined}
          onClick={onOpenActiveList}
          title={onOpenActiveList ? "Open Active Experiments" : undefined}
        >
          <div className="metric-label">Experiments</div>
          <div className="metric-value">{portfolio.total_experiments}</div>
          <div className="metric-sub">{portfolio.active} active · {portfolio.ended} ended</div>
        </div>
        <div
          className="metric-card"
          style={portfolio.needs_attention > 0 && onOpenAttention ? { cursor: "pointer" } : undefined}
          onClick={portfolio.needs_attention > 0 && onOpenAttention ? onOpenAttention : undefined}
          title={portfolio.needs_attention > 0 && onOpenAttention ? "Show experiments needing attention" : undefined}
        >
          <div className="metric-label">Need attention</div>
          <div className={`metric-value ${portfolio.needs_attention > 0 ? "metric-down" : "metric-up"}`}>
            {portfolio.needs_attention}
          </div>
        </div>
        <div
          className="metric-card"
          style={preflight.pending_approvals > 0 && onOpenApprovals ? { cursor: "pointer" } : undefined}
          onClick={preflight.pending_approvals > 0 && onOpenApprovals ? onOpenApprovals : undefined}
          title={preflight.pending_approvals > 0 && onOpenApprovals ? "Open approval queue" : undefined}
        >
          <div className="metric-label">Pending approvals</div>
          <div className={`metric-value ${preflight.pending_approvals > 0 ? "metric-down" : "metric-up"}`}>
            {preflight.pending_approvals}
          </div>
        </div>
        <div
          className="metric-card"
          style={onOpenLessons ? { cursor: "pointer" } : undefined}
          onClick={onOpenLessons}
          title={onOpenLessons ? "Open Lessons library" : undefined}
        >
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
                {health.last_cycle.approvals_created > 0 && onOpenApprovals && (
                  <button
                    type="button"
                    className="inline-link inline-link-danger"
                    style={{ marginLeft: 6, fontSize: 13 }}
                    onClick={onOpenApprovals}
                  >
                    Open queue
                  </button>
                )}
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

      {health.snapshot_gaps.active_count > 0 && (
        <div className={`alert ${health.snapshot_gaps.all_recorded ? "alert-ok" : "alert-warn"}`} style={{ marginBottom: 14 }}>
          <div style={{ fontWeight: 600 }}>
            Snapshots for {health.snapshot_gaps.snapshot_date}:{" "}
            {health.snapshot_gaps.all_recorded
              ? "all active experiments recorded"
              : `${health.snapshot_gaps.missing_count} missing`}
            {!health.snapshot_gaps.all_recorded && onOpenSnapshots && (
              <button
                type="button"
                className="inline-link inline-link-danger"
                style={{ marginLeft: 6, fontSize: 13, fontWeight: 600 }}
                onClick={() => onOpenSnapshots(
                  health.snapshot_gaps.snapshot_date,
                  health.snapshot_gaps.missing[0]?.experiment_id,
                )}
              >
                Record snapshots
              </button>
            )}
          </div>
          {health.snapshot_gaps.missing.length > 0 && (
            <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 13 }}>
              {health.snapshot_gaps.missing.map(m => (
                <li key={m.experiment_id} style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <span>
                    <code>{m.experiment_id}</code> — {m.product_name}
                  </span>
                  {onRecordSnapshot && (
                    <button
                      type="button"
                      className="inline-link inline-link-danger"
                      onClick={() => onRecordSnapshot(health.snapshot_gaps.snapshot_date, m.experiment_id)}
                    >
                      Record
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
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
            {preflight.blockers.map((b, i) => (
              <OperatorMessageListItem key={i} text={b} {...messageHandlers} />
            ))}
          </ul>
        )}
        {preflight.experiments_needing_attention.length > 0 && (
          <div style={{ marginTop: 8, fontSize: 12 }}>
            {preflight.experiments_needing_attention.map(e => (
              <div
                key={e.experiment_id}
                style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}
              >
                <span>
                  <code>{e.experiment_id}</code> — {e.ruling.replace(/_/g, " ")}
                </span>
                {onOpenExperiment && (
                  <button
                    type="button"
                    className="inline-link inline-link-danger"
                    onClick={() => onOpenExperiment(e.experiment_id)}
                  >
                    Details
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
