import { useEffect, useState } from "react";
import { fetchHealth } from "./api/client";
import { Overview } from "./components/Overview";
import { ApprovalQueue } from "./components/ApprovalQueue";
import { ScoreProduct } from "./components/ScoreProduct";
import { ScoreNiche } from "./components/ScoreNiche";
import { UnitEconomics } from "./components/UnitEconomics";
import { ExperimentEvaluator } from "./components/ExperimentEvaluator";
import { OfferSpecPage } from "./components/OfferSpecPage";
import { PrepareOffer } from "./components/PrepareOffer";
import { LiveData } from "./components/LiveData";

type Page =
  | "overview"
  | "approvals"
  | "score"
  | "niche"
  | "economics"
  | "experiment"
  | "spec"
  | "prepare"
  | "live";

function Icon({ d }: { d: string }) {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" dangerouslySetInnerHTML={{ __html: d }} />;
}

const NAV: { id: Page; label: string; icon: string }[] = [
  { id: "overview", label: "Overview", icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { id: "approvals", label: "Approval Queue", icon: '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>' },
  { id: "score", label: "Score Product", icon: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>' },
  { id: "niche", label: "Score Niche", icon: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>' },
  { id: "economics", label: "Unit Economics", icon: '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>' },
  { id: "experiment", label: "Experiment Eval", icon: '<path d="M9 2v6l-5 9a2 2 0 002 3h12a2 2 0 002-3l-5-9V2"/><line x1="9" y1="2" x2="15" y2="2"/>' },
  { id: "spec", label: "Offer Spec", icon: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>' },
  { id: "prepare", label: "Prepare Offer", icon: '<path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>' },
  { id: "live", label: "Live Data", icon: '<path d="M1 6s4-4 11-4 11 4 11 4"/><path d="M1 12s4-4 11-4 11 4 11 4"/><path d="M1 18s4-4 11-4 11 4 11 4"/>' },
];

export function App() {
  const [page, setPage] = useState<Page>("overview");
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  useEffect(() => {
    const check = () =>
      fetchHealth().then(() => setApiOk(true)).catch(() => setApiOk(false));
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
          {NAV.map(n => (
            <button key={n.id} className={`nav-item ${page === n.id ? "active" : ""}`} onClick={() => setPage(n.id)}>
              <Icon d={n.icon} /> {n.label}
            </button>
          ))}
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
        {page === "niche" && <ScoreNiche />}
        {page === "economics" && <UnitEconomics />}
        {page === "experiment" && <ExperimentEvaluator />}
        {page === "spec" && <OfferSpecPage />}
        {page === "prepare" && <PrepareOffer />}
        {page === "live" && <LiveData />}
      </main>
    </div>
  );
}
