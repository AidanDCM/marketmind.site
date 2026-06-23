import { useEffect, useState } from "react";
import { fetchOperatorMistakes, type MistakeRecord } from "../api/client";

export function LessonsLibrary() {
  const [mistakes, setMistakes] = useState<MistakeRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchOperatorMistakes({ limit: 100 })
      .then(r => setMistakes(r.mistakes))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <h2>Lessons Library</h2>
        <p>Recorded experiment lessons — avoid repeating losing patterns.</p>
      </div>
      {loading && <div className="loading-row"><div className="spinner" /></div>}
      {error && <div className="alert alert-error">{error}</div>}
      {!loading && mistakes.length === 0 && !error && (
        <div className="empty"><p>No lessons recorded yet. Save suggestions from Active Experiments.</p></div>
      )}
      <div className="approval-list">
        {mistakes.map(m => (
          <div key={m.mistake_id} className="approval-card">
            <div className="approval-title">{m.summary}</div>
            <div style={{ fontSize: 13, marginTop: 6 }}>{m.lesson}</div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
              <code>{m.experiment_id}</code> · {m.category.replace(/_/g, " ")} · {m.created_at.slice(0, 10)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
