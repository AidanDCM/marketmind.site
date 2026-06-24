import {
  dailyReportLessonActionLabel,
  resolveDailyReportLessonAction,
} from "../dailyReportNavigation";

interface DailyReportLessonsCardProps {
  lessons: string[];
  onOpenLessons?: () => void;
  onOpenApprovals?: () => void;
  onOpenLiveData?: () => void;
}

export function DailyReportLessonsCard({
  lessons,
  onOpenLessons,
  onOpenApprovals,
  onOpenLiveData,
}: DailyReportLessonsCardProps) {
  if (lessons.length === 0) {
    return null;
  }

  return (
    <div className="card" style={{ marginTop: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <div className="card-title" style={{ margin: 0 }}>Lessons</div>
        {onOpenLessons && (
          <button type="button" className="btn-ghost" style={{ fontSize: 13 }} onClick={onOpenLessons}>
            View library
          </button>
        )}
      </div>
      {lessons.map((lesson, i) => {
        const action = resolveDailyReportLessonAction(lesson);
        const canAct = action != null && (
          (action.kind === "approvals" && onOpenApprovals)
          || (action.kind === "live" && onOpenLiveData)
        );
        return (
          <div key={i} className="list-item">
            <div className="bullet" style={{ background: "var(--accent)" }} />
            <div className="list-text">
              {lesson}
              {canAct && action && (
                <button
                  type="button"
                  className="inline-link"
                  style={{ marginLeft: 6, fontSize: 12 }}
                  onClick={() => {
                    if (action.kind === "approvals") {
                      onOpenApprovals?.();
                    } else {
                      onOpenLiveData?.();
                    }
                  }}
                >
                  {dailyReportLessonActionLabel(action)}
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
