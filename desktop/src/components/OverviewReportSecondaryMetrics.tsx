import type { DailyMetrics } from "../api/client";

function fmt$(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function fmtPct(n: number): string {
  return (n * 100).toFixed(1) + "%";
}

interface OverviewReportSecondaryMetricsProps {
  metrics: DailyMetrics;
  onOpenActiveList?: () => void;
}

export function OverviewReportSecondaryMetrics({
  metrics,
  onOpenActiveList,
}: OverviewReportSecondaryMetricsProps) {
  return (
    <div className="metric-grid">
      <div
        className="metric-card"
        style={onOpenActiveList ? { cursor: "pointer" } : undefined}
        onClick={onOpenActiveList}
        title={onOpenActiveList ? "Open Active Experiments" : undefined}
      >
        <div className="metric-label">Contribution Profit</div>
        <div className={`metric-value ${metrics.contribution_profit >= 0 ? "metric-up" : "metric-down"}`}>
          {fmt$(metrics.contribution_profit)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Conversion</div>
        <div className="metric-value">{fmtPct(metrics.conversion_rate)}</div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Add-to-Cart</div>
        <div className="metric-value">{fmtPct(metrics.add_to_cart_rate)}</div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Refund Rate</div>
        <div className={`metric-value ${metrics.refund_rate < 0.05 ? "metric-up" : "metric-down"}`}>
          {fmtPct(metrics.refund_rate)}
        </div>
      </div>
    </div>
  );
}
