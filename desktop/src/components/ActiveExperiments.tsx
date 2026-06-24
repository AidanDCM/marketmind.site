import { useEffect, useState } from "react";
import {
  listActiveExperiments,
  patchExperimentStatus,
  addExperimentNote,
  getExperimentNotes,
  fetchExperimentChecklist,
  fetchExperimentMistakes,
  recordMistake,
  type ActiveExperiment,
  type ExperimentNote,
  type ExperimentChecklist,
  type ExperimentMistakes,
  type MistakeSuggestion,
} from "../api/client";
import { RulingBadge } from "./RulingBadge";

const StatusBadge({ status }: { status: string }) {
  const active = status === "active";
  return (
    <span style={{
      padding: "2px 6px", borderRadius: 4, fontSize: 10, fontWeight: 600,
      background: active ? "var(--green)22" : "var(--text-muted)22",
      color: active ? "var(--green)" : "var(--text-muted)",
      border: `1px solid ${active ? "var(--green)" : "var(--text-muted)"}44`,
    }}>
      {status}
    </span>
  );
}

function ChecklistSection({ experimentId }: { experimentId: string }) {
  const [checklist, setChecklist] = useState<ExperimentChecklist | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchExperimentChecklist(experimentId)
      .then(setChecklist)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [experimentId]);

  if (loading) return <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 14 }}>Loading checklist…</div>;
  if (error) return <div style={{ fontSize: 11, color: "var(--red)", marginTop: 14 }}>{error}</div>;
  if (!checklist) return null;

  return (
    <div style={{ marginTop: 14, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <div className="detail-label">Scale-readiness checklist</div>
        <span style={{
          padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600,
          background: checklist.ready ? "var(--green)22" : "var(--yellow, #f5a623)22",
          color: checklist.ready ? "var(--green)" : "var(--yellow, #f5a623)",
          border: `1px solid ${checklist.ready ? "var(--green)" : "var(--yellow, #f5a623)"}55`,
        }}>
          {checklist.ready ? "Ready to scale" : "Not ready"}
        </span>
      </div>
      {checklist.blockers.length > 0 && (
        <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>
          {checklist.blockers.map((b, i) => <div key={i}>• {b}</div>)}
        </div>
      )}
      {checklist.items.map(item => (
        <div key={item.item_id} style={{ display: "flex", gap: 8, fontSize: 12, marginBottom: 4, alignItems: "flex-start" }}>
          <span style={{ color: item.passed ? "var(--green)" : "var(--red)", fontWeight: 700, flexShrink: 0 }}>
            {item.passed ? "✓" : "✗"}
          </span>
          <div>
            <div>{item.description}</div>
            {item.evidence && (
              <div style={{ color: "var(--text-muted)", fontSize: 11 }}>{item.evidence}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function MistakesSection({ experimentId }: { experimentId: string }) {
  const [data, setData] = useState<ExperimentMistakes | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    fetchExperimentMistakes(experimentId)
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [experimentId]);

  function saveSuggestion(s: MistakeSuggestion) {
    setSaving(s.summary);
    setError(null);
    recordMistake({
      category: s.category,
      experiment_id: experimentId,
      summary: s.summary,
      lesson: s.lesson,
      tags: [...s.tags],
    })
      .then(() => load())
      .catch((err: Error) => setError(err.message))
      .finally(() => setSaving(null));
  }

  if (loading) return <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 14 }}>Loading lessons…</div>;
  if (error) return <div style={{ fontSize: 11, color: "var(--red)", marginTop: 14 }}>{error}</div>;
  if (!data) return null;

  return (
    <div style={{ marginTop: 14, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
      <div className="detail-label" style={{ marginBottom: 8 }}>Lessons learned</div>
      {data.recorded.length === 0 && data.suggested.length === 0 && (
        <div style={{ fontSize: 12, color: "var(--text-muted)" }}>No lessons recorded yet.</div>
      )}
      {data.recorded.map(m => (
        <div key={m.mistake_id} style={{ fontSize: 12, marginBottom: 8 }}>
          <div style={{ fontWeight: 600 }}>{m.summary}</div>
          <div style={{ color: "var(--text-muted)" }}>{m.lesson}</div>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
            {m.category.replace(/_/g, " ")} · {m.created_at.slice(0, 10)}
          </div>
        </div>
      ))}
      {data.suggested.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <div className="detail-label" style={{ marginBottom: 6 }}>Suggested (not yet saved)</div>
          {data.suggested.map((s, i) => (
            <div key={i} style={{ fontSize: 12, marginBottom: 8, display: "flex", gap: 8, alignItems: "flex-start" }}>
              <div style={{ flex: 1 }}>
                <div>{s.summary}</div>
                <div style={{ color: "var(--text-muted)" }}>{s.lesson}</div>
              </div>
              <button
                type="button"
                className="btn-ghost"
                style={{ fontSize: 11, padding: "2px 8px", flexShrink: 0 }}
                disabled={saving === s.summary}
                onClick={() => saveSuggestion(s)}
              >
                {saving === s.summary ? "…" : "Save"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function NotesSection({ experimentId }: { experimentId: string }) {
  const [notes, setNotes] = useState<ExperimentNote[]>([]);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getExperimentNotes(experimentId).then(setNotes).catch(() => {});
  }, [experimentId]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim()) return;
    setSaving(true);
    setError(null);
    addExperimentNote(experimentId, draft.trim())
      .then(note => { setNotes(n => [...n, note]); setDraft(""); })
      .catch((err: Error) => setError(err.message))
      .finally(() => setSaving(false));
  }

  return (
    <div style={{ marginTop: 14, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
      <div className="detail-label" style={{ marginBottom: 8 }}>Notes</div>
      {notes.length === 0 && (
        <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>No notes yet.</div>
      )}
      {notes.map(n => (
        <div key={n.id} style={{ marginBottom: 6, fontSize: 12 }}>
          <span style={{ color: "var(--text-muted)", marginRight: 8 }}>
            {n.created_at.slice(0, 10)}
          </span>
          <span>{n.body}</span>
        </div>
      ))}
      <form onSubmit={submit} style={{ display: "flex", gap: 6, marginTop: 8 }}>
        <input
          value={draft}
          onChange={e => setDraft(e.target.value)}
          placeholder="Add a note…"
          style={{ flex: 1, fontSize: 12 }}
          disabled={saving}
        />
        <button type="submit" className="btn-ghost" disabled={saving || !draft.trim()}
          style={{ fontSize: 12, padding: "4px 10px" }}>
          {saving ? "…" : "Add"}
        </button>
      </form>
      {error && <div style={{ fontSize: 11, color: "var(--red)", marginTop: 4 }}>{error}</div>}
    </div>
  );
}

function ExperimentCard({ exp, onStatusChange }: { exp: ActiveExperiment; onStatusChange: () => void }) {
  const [open, setOpen] = useState(false);
  const [patching, setPatching] = useState(false);
  const [patchError, setPatchError] = useState<string | null>(null);
  const cacOver = exp.actual_cac !== null && exp.actual_cac > exp.break_even_cac;

  function toggleStatus(e: React.MouseEvent) {
    e.stopPropagation();
    const next = exp.status === "active" ? "ended" : "active";
    setPatching(true);
    setPatchError(null);
    patchExperimentStatus(exp.experiment_id, next)
      .then(() => onStatusChange())
      .catch((err: Error) => setPatchError(err.message))
      .finally(() => setPatching(false));
  }

  return (
    <div className="approval-card" style={{ cursor: "pointer" }} onClick={() => setOpen(o => !o)}>
      <div className="approval-header">
        <div style={{ minWidth: 0 }}>
          <div className="approval-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <code style={{ fontSize: 13 }}>{exp.experiment_id}</code>
            <StatusBadge status={exp.status} />
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 3 }}>{exp.product_name}</div>
        </div>
        <div className="approval-meta" style={{ flexShrink: 0 }}>
          <RulingBadge ruling={exp.ruling} />
          {exp.actual_cac !== null && (
            <span style={{ fontSize: 12, color: cacOver ? "var(--red)" : "var(--green)", fontWeight: 600 }}>
              CAC ${exp.actual_cac.toFixed(2)}
            </span>
          )}
          <svg className={`chevron ${open ? "open" : ""}`} width="14" height="14" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>

      {open && (
        <div className="approval-body" onClick={e => e.stopPropagation()}>
          <div className="approval-detail">
            <div>
              <div className="detail-label">Break-even CAC</div>
              <div className="detail-value">${exp.break_even_cac.toFixed(2)}</div>
            </div>
            <div>
              <div className="detail-label">Latest snapshot</div>
              <div className="detail-value">{exp.latest_snapshot_date ?? "—"}</div>
            </div>
            <div>
              <div className="detail-label">Started</div>
              <div className="detail-value">{exp.started_at.slice(0, 10)}</div>
            </div>
            {exp.ended_at && (
              <div>
                <div className="detail-label">Ended</div>
                <div className="detail-value">{exp.ended_at.slice(0, 10)}</div>
              </div>
            )}
          </div>
          {exp.risks.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div className="detail-label" style={{ marginBottom: 6 }}>Risks</div>
              {exp.risks.map((r, i) => (
                <div key={i} className="list-item">
                  <div className="bullet risk" />
                  <div className="list-text" style={{ fontSize: 12 }}>{r}</div>
                </div>
              ))}
            </div>
          )}
          <div style={{ marginTop: 14, display: "flex", gap: 8, alignItems: "center" }}>
            <button
              className={`btn-ghost ${patching ? "disabled" : ""}`}
              disabled={patching}
              onClick={toggleStatus}
              style={{ fontSize: 12 }}
            >
              {patching ? "…" : exp.status === "active" ? "End experiment" : "Reactivate"}
            </button>
            {patchError && (
              <span style={{ fontSize: 11, color: "var(--red)" }}>{patchError}</span>
            )}
          </div>
          <NotesSection experimentId={exp.experiment_id} />
          <MistakesSection experimentId={exp.experiment_id} />
          {exp.status === "active" && <ChecklistSection experimentId={exp.experiment_id} />}
        </div>
      )}
    </div>
  );
}

const STATUS_FILTERS = ["all", "active", "ended"] as const;

export function ActiveExperiments() {
  const [experiments, setExperiments] = useState<ActiveExperiment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "active" | "ended">("active");

  function load() {
    setLoading(true);
    setError(null);
    listActiveExperiments()
      .then(setExperiments)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  const visible = experiments.filter(e =>
    filter === "all" ? true :
    filter === "active" ? e.status === "active" :
    e.status !== "active"
  );

  const needsAction = experiments.filter(e =>
    e.ruling === "kill" || e.ruling === "pause_ads" || e.ruling === "scale_requires_approval"
  ).length;

  return (
    <div>
      <h2>Active Experiments</h2>
      <p className="dim">All experiments with their latest ruling from the rule engine.</p>

      {needsAction > 0 && (
        <div className="alert alert-warn" style={{ marginTop: "1rem" }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          {needsAction} experiment{needsAction !== 1 ? "s" : ""} require attention (kill / pause / scale).
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1.25rem" }}>
        <div className="filter-bar">
          {STATUS_FILTERS.map(f => (
            <button key={f} className={`filter-btn ${filter === f ? "active" : ""}`}
              onClick={() => setFilter(f)}>
              {f}
            </button>
          ))}
        </div>
        <button className="btn-ghost" onClick={load}>↺ Refresh</button>
      </div>

      {loading && <div className="loading-row"><div className="spinner" /></div>}
      {error && <div className="alert alert-error" style={{ marginTop: "1rem" }}>{error}</div>}

      {!loading && visible.length === 0 && !error && (
        <div className="empty" style={{ marginTop: "2rem" }}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M9 2v6l-5 9a2 2 0 002 3h12a2 2 0 002-3l-5-9V2"/>
            <line x1="9" y1="2" x2="15" y2="2"/>
          </svg>
          <p>No {filter === "all" ? "" : filter} experiments. Record a snapshot to create one.</p>
        </div>
      )}

      <div className="approval-list" style={{ marginTop: "1rem" }}>
        {visible.map(e => <ExperimentCard key={e.experiment_id} exp={e} onStatusChange={load} />)}
      </div>
    </div>
  );
}
