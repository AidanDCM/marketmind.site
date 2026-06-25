interface OverviewTrendEmptyStateProps {
  asOf: string;
  attentionOnly: boolean;
  onOpenActiveList?: () => void;
}

export function OverviewTrendEmptyState({
  asOf,
  attentionOnly,
  onOpenActiveList,
}: OverviewTrendEmptyStateProps) {
  return (
    <div style={{ color: "var(--text-muted)", fontSize: 13 }}>
      No active experiments need attention for {asOf}.
      {attentionOnly && onOpenActiveList && (
        <button
          type="button"
          className="inline-link"
          style={{ marginLeft: 6, fontSize: 13 }}
          onClick={onOpenActiveList}
        >
          View all experiments
        </button>
      )}
    </div>
  );
}
