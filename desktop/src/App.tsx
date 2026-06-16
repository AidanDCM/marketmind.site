import { useEffect, useState } from "react";
import { fetchHealth } from "./api/client";
import { Overview } from "./components/Overview";
import { ApprovalQueue } from "./components/ApprovalQueue";
import { ScoreProduct } from "./components/ScoreProduct";

type Page = "overview" | "approvals" | "score";

function IconChart() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>;
}
function IconQueue() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>;
}
function IconScore() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>;
}

export function App() {
  const [page, setPage] = useState<Page>("overview");
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  useEffect(() => {
    const check = () =>
      fetchHealth()
        .then(() => setApiOk(true))
        .catch(() => setApiOk(false));
    check();
    const id = setInterval(check, 15_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>MarketMind</h1>
          <span>Autopilot Dashboard</span>
        </div>

        <nav className="sidebar-nav">
          <button className={`nav-item ${page === "overview" ? "active" : ""}`} onClick={() => setPage("overview")}>
            <IconChart /> Overview
          </button>
          <button className={`nav-item ${page === "approvals" ? "active" : ""}`} onClick={() => setPage("approvals")}>
            <IconQueue /> Approval Queue
          </button>
          <button className={`nav-item ${page === "score" ? "active" : ""}`} onClick={() => setPage("score")}>
            <IconScore /> Score Product
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="api-status">
            <div className={`dot ${apiOk === true ? "ok" : ""}`} />
            {apiOk === null ? "Connecting…" : apiOk ? "API connected" : "API offline — start uvicorn"}
          </div>
        </div>
      </aside>

      <main className="main">
        {page === "overview" && <Overview />}
        {page === "approvals" && <ApprovalQueue />}
        {page === "score" && <ScoreProduct />}
      </main>
    </div>
  );
}
