import {
  buildExperimentProductLookup,
  resolveExperimentIdForReportLine,
  type ExperimentProductLookup,
} from "../dailyReportNavigation";

interface DailyReportInsightListProps {
  title: string;
  items: string[];
  bulletClass: "risk" | "rec";
  experiments: ExperimentProductLookup[];
  onOpenActive?: (experimentId: string) => void;
}

export function DailyReportInsightList({
  title,
  items,
  bulletClass,
  experiments,
  onOpenActive,
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
          const experimentId = resolveExperimentIdForReportLine(item, lookup);
          return (
            <div key={i} className="list-item">
              <div className={`bullet ${bulletClass}`} />
              <div className="list-text">
                {item}
                {experimentId && onOpenActive && (
                  <button
                    type="button"
                    className="inline-link"
                    style={{ marginLeft: 6, fontSize: 12 }}
                    onClick={() => onOpenActive(experimentId)}
                  >
                    View experiment
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
