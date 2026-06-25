import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import { OperatorHealthPanelView, type OperatorHealthPanel } from "./OperatorHealthPanel";

const baseHealth: OperatorHealthPanel = {
  safe_to_operate: false,
  warnings: [],
  preflight: {
    safe_to_operate: false,
    pending_approvals: 2,
    experiments_needing_attention: [],
    operator_log_exists: true,
    blockers: ["2 pending approval(s) have not been reviewed"],
    summary: "ATTENTION REQUIRED: 2 pending approval(s)",
  },
  integrations: {
    gmail: { mode: "simulate", live_ready: false, dry_run: true },
    stripe: { configured: false, dry_run: true, live_ready: false },
    shopify: { configured: false, read_only: true, live_ready: false },
    live_writes: { enabled: false },
  },
  portfolio: {
    total_experiments: 3,
    active: 2,
    ended: 1,
    needs_attention: 0,
    lessons_recorded: 4,
  },
  ad_spend: { has_data: false, summary: null },
  checklist: { min_visits: 100, min_orders: 5, min_spend: 50 },
  last_cycle: {
    event_id: "evt-1",
    created_at: "2026-06-23T12:00:00Z",
    date: "2026-06-23",
    experiments_evaluated: 2,
    approvals_created: 1,
  },
  snapshot_gaps: {
    snapshot_date: "2026-06-23",
    active_count: 2,
    missing_count: 0,
    missing: [],
    all_recorded: true,
  },
};

describe("OperatorHealthPanelView", () => {
  it("opens approval queue from pending approvals metric", () => {
    const onOpenApprovals = vi.fn();
    render(
      <OperatorHealthPanelView health={baseHealth} onOpenApprovals={onOpenApprovals} />,
    );
    fireEvent.click(screen.getByTitle("Open approval queue"));
    expect(onOpenApprovals).toHaveBeenCalledOnce();
  });

  it("opens approval queue from last cycle queued approvals link", () => {
    const onOpenApprovals = vi.fn();
    render(
      <OperatorHealthPanelView health={baseHealth} onOpenApprovals={onOpenApprovals} />,
    );
    const lastCycle = screen.getByText("Last daily cycle").closest(".card")!;
    fireEvent.click(within(lastCycle as HTMLElement).getByRole("button", { name: "Open queue" }));
    expect(onOpenApprovals).toHaveBeenCalledOnce();
  });

  it("opens snapshot recorder from missing snapshot gaps header", () => {
    const onOpenSnapshots = vi.fn();
    const health: OperatorHealthPanel = {
      ...baseHealth,
      snapshot_gaps: {
        snapshot_date: "2026-06-23",
        active_count: 2,
        missing_count: 1,
        missing: [{ experiment_id: "exp-missing", product_name: "Widget" }],
        all_recorded: false,
      },
    };
    render(
      <OperatorHealthPanelView health={health} onOpenSnapshots={onOpenSnapshots} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Record snapshots" }));
    expect(onOpenSnapshots).toHaveBeenCalledWith("2026-06-23", "exp-missing");
  });

  it("opens experiment details from missing snapshot gap row", () => {
    const onOpenExperiment = vi.fn();
    const health: OperatorHealthPanel = {
      ...baseHealth,
      snapshot_gaps: {
        snapshot_date: "2026-06-23",
        active_count: 2,
        missing_count: 1,
        missing: [{ experiment_id: "exp-missing", product_name: "Widget" }],
        all_recorded: false,
      },
    };
    render(
      <OperatorHealthPanelView health={health} onOpenExperiment={onOpenExperiment} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Details" }));
    expect(onOpenExperiment).toHaveBeenCalledWith("exp-missing");
  });

  it("opens active experiments from experiments metric", () => {
    const onOpenActiveList = vi.fn();
    render(
      <OperatorHealthPanelView health={baseHealth} onOpenActiveList={onOpenActiveList} />,
    );
    fireEvent.click(screen.getByTitle("Open Active Experiments"));
    expect(onOpenActiveList).toHaveBeenCalledOnce();
  });

  it("opens lessons library from lessons metric", () => {
    const onOpenLessons = vi.fn();
    render(
      <OperatorHealthPanelView health={baseHealth} onOpenLessons={onOpenLessons} />,
    );
    fireEvent.click(screen.getByTitle("Open Lessons library"));
    expect(onOpenLessons).toHaveBeenCalledOnce();
  });

  it("opens import history from imported ad spend metric", () => {
    const onOpenImportHistory = vi.fn();
    const health: OperatorHealthPanel = {
      ...baseHealth,
      ad_spend: {
        has_data: true,
        summary: {
          batch_id: 1,
          source: "csv",
          pulled_at: "2026-06-23T10:00:00Z",
          campaigns: 3,
          total_spend: 1200,
          total_clicks: 400,
          total_impressions: 10000,
          total_purchases: 12,
          total_revenue: 2400,
        },
      },
    };
    render(
      <OperatorHealthPanelView health={health} onOpenImportHistory={onOpenImportHistory} />,
    );
    fireEvent.click(screen.getByTitle("Open Import History"));
    expect(onOpenImportHistory).toHaveBeenCalledOnce();
  });

  it("opens live data from integration metrics", () => {
    const onOpenLiveData = vi.fn();
    render(
      <OperatorHealthPanelView health={baseHealth} onOpenLiveData={onOpenLiveData} />,
    );
    fireEvent.click(screen.getAllByTitle("Open Live Data")[0]);
    expect(onOpenLiveData).toHaveBeenCalledOnce();
  });

  it("prompts import history when active experiments have no ad spend data", () => {
    const onOpenImportHistory = vi.fn();
    render(
      <OperatorHealthPanelView health={baseHealth} onOpenImportHistory={onOpenImportHistory} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Import ads" }));
    expect(onOpenImportHistory).toHaveBeenCalledOnce();
  });

  it("opens active experiments from last cycle evaluated count link", () => {
    const onOpenActiveList = vi.fn();
    render(
      <OperatorHealthPanelView health={baseHealth} onOpenActiveList={onOpenActiveList} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "View experiments" }));
    expect(onOpenActiveList).toHaveBeenCalledOnce();
  });

  it("opens snapshots when all active experiments are recorded", () => {
    const onOpenSnapshots = vi.fn();
    render(
      <OperatorHealthPanelView health={baseHealth} onOpenSnapshots={onOpenSnapshots} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "View snapshots" }));
    expect(onOpenSnapshots).toHaveBeenCalledWith("2026-06-23");
  });

  it("opens attention experiments from preflight summary link", () => {
    const onOpenAttention = vi.fn();
    const health: OperatorHealthPanel = {
      ...baseHealth,
      preflight: {
        ...baseHealth.preflight,
        experiments_needing_attention: [
          { experiment_id: "exp-kill", product_name: "Widget", ruling: "kill", risks: [] },
        ],
      },
    };
    render(
      <OperatorHealthPanelView health={health} onOpenAttention={onOpenAttention} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Show attention" }));
    expect(onOpenAttention).toHaveBeenCalledOnce();
  });

  it("opens approval queue from preflight summary link", () => {
    const onOpenApprovals = vi.fn();
    render(
      <OperatorHealthPanelView health={baseHealth} onOpenApprovals={onOpenApprovals} />,
    );
    const preflightAlert = screen.getByText(/ATTENTION REQUIRED/).closest(".alert")!;
    fireEvent.click(
      within(preflightAlert as HTMLElement).getAllByRole("button", { name: "Open queue" })[0],
    );
    expect(onOpenApprovals).toHaveBeenCalledOnce();
  });

  it("links integration warnings to Live Data", () => {
    const onOpenLiveData = vi.fn();
    const health: OperatorHealthPanel = {
      ...baseHealth,
      warnings: ["MARKETMIND_ENABLE_LIVE_WRITES=true but Gmail is not live-ready"],
    };
    render(
      <OperatorHealthPanelView health={health} onOpenLiveData={onOpenLiveData} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Check Live Data" }));
    expect(onOpenLiveData).toHaveBeenCalledOnce();
  });

  it("links snapshot gap warnings to snapshot recorder", () => {
    const onOpenSnapshots = vi.fn();
    const health: OperatorHealthPanel = {
      ...baseHealth,
      warnings: ["1 active experiment(s) missing snapshot for 2026-06-23: exp_gap"],
      snapshot_gaps: {
        snapshot_date: "2026-06-23",
        active_count: 1,
        missing_count: 1,
        missing: [{ experiment_id: "exp_gap", product_name: "Widget" }],
        all_recorded: false,
      },
    };
    render(
      <OperatorHealthPanelView health={health} onOpenSnapshots={onOpenSnapshots} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Record snapshot" }));
    expect(onOpenSnapshots).toHaveBeenCalledWith("2026-06-23", "exp_gap");
  });
});
