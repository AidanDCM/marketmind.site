import {
  buildExperimentProductLookup,
  dailyReportLineActionLabel,
  resolveDailyReportLineAction,
  type ExperimentProductLookup,
} from "../dailyReportNavigation";

interface DailyReportInsightListProps {
  title: string;
  items: string[];
  bulletClass: "risk" | "rec";
  experiments: ExperimentProductLookup[];
  onOpenActive?: (experimentId: string) => void;
  onOpenApprovals?: () => void;
}

export function DailyReportInsightList({
  title,
  items,
  bulletClass,
  experiments,
  onOpenActive,
  onOpenApprovals,
}: DailyReportInsightListProps) {
  const lookup = buildExperimentProductLookup([experiments]);

  return (
    <div className="card">
      <div className="card-title">{title}</div>
      {items.length === 0 ? (
        <div style={{ color: "var(--text-muted)", fontSize: 13 }}>
          {title === "Risks" ? "No risks flagged" : "No recommendations"}
        </div>
      ) : (
        items.map((item, i) => {
          const action = resolveDailyReportLineAction(item, lookup);
          const canAct = action != null && (
            (action.kind === "experiment" && onOpenActive)
            || (action.kind === "approvals" && onOpenApprovals)
          );
          return (
            <div key={i} className="list-item">
              <div className={`bullet ${bulletClass}`} />
              <div className="list-text">
                {item}
                {canAct && action && (
                  <button
                    type="button"
                    className="inline-link"
                    style={{ marginLeft: 6, fontSize: 12 }}
                    onClick={() => {
                      if (action.kind === "approvals") {
                        onOpenApprovals?.();
                      } else {
                        onOpenActive?.(action.experimentId);
                      }
                    }}
                  >
                    {dailyReportLineActionLabel(action)}
                  </button>
                )}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
