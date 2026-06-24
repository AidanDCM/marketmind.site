import { useEffect, useState } from "react";
import { fetchHealth } from "./api/client";
import { readTrendDaysPreference } from "./components/overviewPreferences";
import { useExperimentAttentionCount } from "./useExperimentAttentionCount";
import { usePendingApprovalSummary } from "./usePendingApprovalSummary";
import { Overview } from "./components/Overview";
import { ApprovalQueue } from "./components/ApprovalQueue";
import { ScoreProduct } from "./components/ScoreProduct";
import { ScoreNiche } from "./components/ScoreNiche";
import { UnitEconomics } from "./components/UnitEconomics";
import { ExperimentEvaluator } from "./components/ExperimentEvaluator";
import { OfferSpecPage } from "./components/OfferSpecPage";
import { PrepareOffer } from "./components/PrepareOffer";
import { LiveData } from "./components/LiveData";
import { ImportHistory } from "./components/ImportHistory";
import { SnapshotRecorder } from "./components/SnapshotRecorder";
import { SnapshotTrend } from "./components/SnapshotTrend";
import { ActiveExperiments } from "./components/ActiveExperiments";
import { LessonsLibrary } from "./components/LessonsLibrary";
import { SupplierOutreach } from "./components/SupplierOutreach";
import type { Page, PageContext } from "./navigation";

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
  { id: "supplier", label: "Supplier Outreach", icon: '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>' },
  { id: "lessons", label: "Lessons", icon: '<path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/>' },
  { id: "live", label: "Live Data", icon: '<path d="M1 6s4-4 11-4 11 4 11 4"/><path d="M1 12s4-4 11-4 11 4 11 4"/><path d="M1 18s4-4 11-4 11 4 11 4"/>' },
  { id: "history", label: "Import History", icon: '<path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/>' },
  { id: "snapshots", label: "Snapshots", icon: '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>' },
  { id: "trend", label: "Trend", icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>' },
  { id: "active", label: "Active Experiments", icon: '<path d="M9 2v6l-5 9a2 2 0 002 3h12a2 2 0 002-3l-5-9V2"/><line x1="9" y1="2" x2="15" y2="2"/><circle cx="18" cy="5" r="3" fill="currentColor"/>' },
];

export function App() {
  const [page, setPage] = useState<Page>("overview");
  const [pageContext, setPageContext] = useState<PageContext | null>(null);
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [navRefresh, setNavRefresh] = useState(0);
  const attentionCount = useExperimentAttentionCount(apiOk, navRefresh);
  const pending = usePendingApprovalSummary(apiOk, navRefresh);

  function navigate(next: Page, context?: PageContext) {
    setPageContext(context ?? null);
    setPage(next);
  }

  function openTrendFromOverview(experimentId: string, trendDays: number) {
    navigate("trend", { experimentId, trendDays });
  }

  function openActiveFromOverview(experimentId: string) {
    navigate("active", { experimentId });
  }

  function openApprovals(focusApprovalId?: string) {
    navigate("approvals", focusApprovalId ? { focusApprovalId } : undefined);
  }

  function openSnapshots(snapshotDate: string, experimentId?: string) {
    navigate("snapshots", { snapshotDate, experimentId });
  }

  function bumpNavRefresh() {
    setNavRefresh((n) => n + 1);
  }

  function openAttentionExperiments() {
    navigate("active", { attentionOnly: true });
  }

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
            <button key={n.id} className={`nav-item ${page === n.id ? "active" : ""}`} onClick={() => navigate(n.id)}>
              <Icon d={n.icon} />
              <span className="nav-label">{n.label}</span>
              {n.id === "approvals" && pending.count > 0 && (
                <span
                  className="nav-badge nav-badge-warn"
                  title="Open first pending approval"
                  onClick={(e) => {
                    e.stopPropagation();
                    openApprovals(pending.firstApprovalId ?? undefined);
                  }}
                >
                  {pending.count}
                </span>
              )}
              {n.id === "active" && attentionCount > 0 && (
                <span
                  className="nav-badge"
                  title="Show experiments needing attention"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate("active", { attentionOnly: true });
                  }}
                >
                  {attentionCount}
                </span>
              )}
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
        {page === "overview" && (
          <Overview
            onOpenTrend={openTrendFromOverview}
            onOpenActive={openActiveFromOverview}
            onOpenApprovals={openApprovals}
            onOpenAttention={openAttentionExperiments}
            onOpenSnapshots={openSnapshots}
          />
        )}
        {page === "approvals" && (
          <ApprovalQueue
            key={pageContext?.focusApprovalId ?? "approvals-default"}
            focusApprovalId={pageContext?.focusApprovalId}
            onQueueChanged={bumpNavRefresh}
          />
        )}
        {page === "score" && <ScoreProduct />}
        {page === "niche" && <ScoreNiche />}
        {page === "economics" && <UnitEconomics />}
        {page === "experiment" && <ExperimentEvaluator />}
        {page === "spec" && <OfferSpecPage />}
        {page === "prepare" && <PrepareOffer />}
        {page === "supplier" && <SupplierOutreach />}
        {page === "lessons" && <LessonsLibrary />}
        {page === "live" && <LiveData />}
        {page === "history" && <ImportHistory />}
        {page === "snapshots" && (
          <SnapshotRecorder
            key={`${pageContext?.snapshotDate ?? "snap-default"}-${pageContext?.experimentId ?? ""}`}
            initialSnapshotDate={pageContext?.snapshotDate}
            initialExperimentId={pageContext?.experimentId}
          />
        )}
        {page === "trend" && (
          <SnapshotTrend
            key={pageContext?.experimentId ?? "trend-default"}
            initialExperimentId={pageContext?.experimentId}
            initialDays={pageContext?.trendDays}
          />
        )}
        {page === "active" && (
          <ActiveExperiments
            key={`${pageContext?.experimentId ?? "active-default"}-${pageContext?.attentionOnly ? "attention" : "all"}`}
            focusExperimentId={pageContext?.experimentId}
            initialAttentionOnly={pageContext?.attentionOnly ?? false}
            onOpenTrend={(experimentId) => openTrendFromOverview(experimentId, readTrendDaysPreference())}
            onExperimentsChanged={bumpNavRefresh}
          />
        )}
      </main>
    </div>
  );
}
