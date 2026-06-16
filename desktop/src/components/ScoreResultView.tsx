import type { ScoreResult, CriterionScore } from "../api/client";

function scoreColor(s01: number): string {
  if (s01 >= 0.7) return "var(--green)";
  if (s01 >= 0.4) return "var(--yellow)";
  return "var(--red)";
}

function CriteriaRow({ c }: { c: CriterionScore }) {
  const pct = Math.min(100, c.raw * 100);
  return (
    <tr>
      <td>{c.name.replace(/_/g, " ")}</td>
      <td>
        <div className="score-bar" style={{ width: 80 }}>
          <div className="score-fill" style={{ width: `${pct}%`, background: scoreColor(c.raw) }} />
        </div>
      </td>
      <td style={{ color: scoreColor(c.raw), fontWeight: 600 }}>{(c.raw * 10).toFixed(1)}</td>
      <td style={{ color: "var(--text-muted)", fontSize: 12 }}>{(c.weight * 100).toFixed(0)}%</td>
      <td style={{ color: "var(--text-muted)", fontSize: 12 }}>{c.reason}</td>
    </tr>
  );
}

export function ScoreResultView({ result }: { result: ScoreResult }) {
  const vClass = result.verdict.toLowerCase();
  return (
    <>
      <div className={`verdict ${vClass}`}>
        <div className="verdict-label">Verdict — {result.name}</div>
        <div className="verdict-value">{result.verdict.toUpperCase()}</div>
        <div className="verdict-score">
          Score {(result.overall_score * 10).toFixed(1)} / 10 &nbsp;·&nbsp; Confidence {(result.confidence * 10).toFixed(1)} / 10
        </div>
        {result.channel && (
          <div style={{ marginTop: 10 }}>
            <span className="channel">
              {result.channel.channel.replace(/_/g, " ")} · {result.channel.strategy.replace(/_/g, " ")}
            </span>
          </div>
        )}
      </div>

      <div className="card" style={{ marginBottom: 14 }}>
        <div className="card-title">Why</div>
        <div className="spec-text">{result.reason_summary}</div>
        {result.channel && (
          <div className="spec-text" style={{ marginTop: 8, color: "var(--text-muted)" }}>
            {result.channel.reason}
          </div>
        )}
      </div>

      {result.risks.length > 0 && (
        <div className="card" style={{ marginBottom: 14 }}>
          <div className="card-title">Risks</div>
          {result.risks.map((r, i) => (
            <div key={i} className="list-item">
              <div className="bullet risk" />
              <div className="list-text">{r.replace(/_/g, " ")}</div>
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <div className="card-title">Criterion Breakdown</div>
        <table className="criteria-table">
          <thead>
            <tr>
              <th>Criterion</th>
              <th></th>
              <th>Score</th>
              <th>Weight</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {result.criteria.map((c, i) => <CriteriaRow key={i} c={c} />)}
          </tbody>
        </table>
      </div>
    </>
  );
}
