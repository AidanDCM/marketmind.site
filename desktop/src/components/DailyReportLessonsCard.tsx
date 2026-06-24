interface DailyReportLessonsCardProps {
  lessons: string[];
  onOpenLessons?: () => void;
}

export function DailyReportLessonsCard({ lessons, onOpenLessons }: DailyReportLessonsCardProps) {
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
      {lessons.map((lesson, i) => (
        <div key={i} className="list-item">
          <div className="bullet" style={{ background: "var(--accent)" }} />
          <div className="list-text">{lesson}</div>
        </div>
      ))}
    </div>
  );
}
