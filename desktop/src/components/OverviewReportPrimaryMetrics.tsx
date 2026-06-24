import type { DailyMetrics } from "../api/client";

function fmt$(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

interface OverviewReportPrimaryMetricsProps {
  metrics: DailyMetrics;
  date: string;
  onOpenImportHistory?: () => void;
  onOpenLiveData?: () => void;
  onOpenActiveList?: () => void;
}

export function OverviewReportPrimaryMetrics({
  metrics,
  date,
  onOpenImportHistory,
  onOpenLiveData,
  onOpenActiveList,
}: OverviewReportPrimaryMetricsProps) {
  return (
    <div className="metric-grid">
      <div
        className="metric-card"
        style={onOpenLiveData ? { cursor: "pointer" } : undefined}
        onClick={onOpenLiveData}
        title={onOpenLiveData ? "Open Live Data" : undefined}
      >
        <div className="metric-label">Orders</div>
        <div className="metric-value">{metrics.orders}</div>
        <div className="metric-sub">for {date}</div>
      </div>
      <div
        className="metric-card"
        style={onOpenLiveData ? { cursor: "pointer" } : undefined}
        onClick={onOpenLiveData}
        title={onOpenLiveData ? "Open Live Data" : undefined}
      >
        <div className="metric-label">Revenue</div>
        <div className="metric-value">{fmt$(metrics.revenue)}</div>
        <div className="metric-sub">gross</div>
      </div>
      <div
        className="metric-card"
        style={onOpenImportHistory ? { cursor: "pointer" } : undefined}
        onClick={onOpenImportHistory}
        title={onOpenImportHistory ? "Open Import History" : undefined}
      >
        <div className="metric-label">Ad Spend</div>
        <div className="metric-value metric-down">{fmt$(metrics.ad_spend)}</div>
        <div className="metric-sub">total spend</div>
      </div>
      <div
        className="metric-card"
        style={onOpenActiveList ? { cursor: "pointer" } : undefined}
        onClick={onOpenActiveList}
        title={onOpenActiveList ? "Open Active Experiments" : undefined}
      >
        <div className="metric-label">CAC</div>
        <div className="metric-value">{fmt$(metrics.cac)}</div>
        <div className="metric-sub">per order</div>
      </div>
    </div>
  );
}
