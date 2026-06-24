import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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
    fireEvent.click(screen.getByRole("button", { name: "Open queue" }));
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
});
