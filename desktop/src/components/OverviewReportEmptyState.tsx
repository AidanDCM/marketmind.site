interface OverviewReportEmptyStateProps {
  date: string;
  onOpenSnapshots: (snapshotDate: string) => void;
  onOpenScoreProduct?: () => void;
}

export function OverviewReportEmptyState({
  date,
  onOpenSnapshots,
  onOpenScoreProduct,
}: OverviewReportEmptyStateProps) {
  return (
    <div className="empty">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <line x1="9" y1="9" x2="15" y2="9" />
        <line x1="9" y1="13" x2="15" y2="13" />
        <line x1="9" y1="17" x2="12" y2="17" />
      </svg>
      <p>No report data for {date}</p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", marginTop: 8 }}>
        <button type="button" className="btn-ghost" onClick={() => onOpenSnapshots(date)}>
          Record a snapshot for {date}
        </button>
        {onOpenScoreProduct && (
          <button type="button" className="btn-ghost" onClick={onOpenScoreProduct}>
            Score a product
          </button>
        )}
      </div>
    </div>
  );
}
