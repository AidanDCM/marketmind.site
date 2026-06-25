import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Overview } from "./Overview";
import type {
  ApprovalRecord,
  DailyReport,
  ExperimentTrendSummary,
  OperatorHealthPanel,
  OperatorReadiness,
} from "../api/client";

vi.mock("../api/client", () => ({
  fetchDailyReport: vi.fn(),
  fetchPendingApprovals: vi.fn(),
  fetchOperatorHealthPanel: vi.fn(),
  fetchOperatorReadiness: vi.fn(),
  fetchExperimentTrendSummary: vi.fn(),
  runOperatorDailyCycle: vi.fn(),
}));

vi.mock("./overviewPreferences", () => ({
  ATTENTION_ONLY_KEY: "marketmind_attention_only",
  TREND_DAYS_KEY: "marketmind_trend_days",
  OVERVIEW_DATE_KEY: "marketmind_overview_date",
  TREND_DAY_OPTIONS: [7, 14, 30],
  readAttentionOnlyPreference: () => false,
  readOverviewDatePreference: () => "2026-06-23",
  readTrendDaysPreference: () => 14,
  isSnapshotStale: (snapshotDate: string | null, asOf: string) =>
    snapshotDate != null && snapshotDate < asOf,
}));

import {
  fetchDailyReport,
  fetchPendingApprovals,
  fetchOperatorHealthPanel,
  fetchOperatorReadiness,
  fetchExperimentTrendSummary,
} from "../api/client";

const baseHealth: OperatorHealthPanel = {
  safe_to_operate: true,
  warnings: [],
  preflight: {
    safe_to_operate: true,
    pending_approvals: 0,
    experiments_needing_attention: [],
    operator_log_exists: true,
    blockers: [],
    summary: "OK",
  },
  integrations: {
    gmail: { mode: "simulate", live_ready: false, dry_run: true },
    stripe: { configured: false, dry_run: true, live_ready: false },
    shopify: { configured: false, read_only: true, live_ready: false },
    live_writes: { enabled: false },
  },
  portfolio: {
    total_experiments: 1,
    active: 1,
    ended: 0,
    needs_attention: 0,
    lessons_recorded: 0,
  },
  ad_spend: { has_data: false, summary: null },
  checklist: { min_visits: 100, min_orders: 5, min_spend: 50 },
  last_cycle: null,
  snapshot_gaps: {
    snapshot_date: "2026-06-23",
    active_count: 1,
    missing_count: 0,
    missing: [],
    all_recorded: true,
  },
};

const baseReadiness: OperatorReadiness = {
  ready: true,
  blockers: [],
  warnings: [],
  safe_to_operate: true,
  gmail: { mode: "simulate", live_ready: false },
  commerce: {
    stripe: { configured: false, live_ready: false },
    shopify: { configured: false, live_ready: false },
  },
  snapshot_gaps: baseHealth.snapshot_gaps,
};

const baseMetrics: DailyReport["metrics"] = {
  date: "2026-06-23",
  revenue: 1200,
  orders: 8,
  ad_spend: 300,
  refund_count: 0,
  contribution_profit: 400,
  cac: 37.5,
  conversion_rate: 0.04,
  add_to_cart_rate: 0.12,
  refund_rate: 0.01,
};

const baseTrend: ExperimentTrendSummary = {
  days: 14,
  as_of: "2026-06-23",
  needs_attention_count: 1,
  experiments: [
    {
      experiment_id: "exp-trend",
      product_name: "Widget",
      break_even_cac: 50,
      snapshot_count: 3,
      latest_snapshot_date: "2026-06-22",
      latest_cac: 60,
      prior_cac: 55,
      cac_direction: "up",
      ruling: "pause_ads",
      above_break_even: true,
      needs_attention: true,
    },
  ],
};

function mockOverviewData(options: {
  report?: DailyReport | null;
  pending?: ApprovalRecord[];
  trendSummary?: ExperimentTrendSummary;
}) {
  const report = options.report === undefined
    ? ({
        date: "2026-06-23",
        metrics: baseMetrics,
        pending_approvals: [],
        recommendations: [],
        risks: [],
        lessons: [],
      } satisfies DailyReport)
    : options.report;

  vi.mocked(fetchDailyReport).mockResolvedValue(report as DailyReport);
  vi.mocked(fetchPendingApprovals).mockResolvedValue(options.pending ?? []);
  vi.mocked(fetchOperatorHealthPanel).mockResolvedValue(baseHealth);
  vi.mocked(fetchOperatorReadiness).mockResolvedValue(baseReadiness);
  vi.mocked(fetchExperimentTrendSummary).mockResolvedValue(
    options.trendSummary ?? baseTrend,
  );
}

async function renderOverview(handlers: Partial<{
  onOpenTrend: (experimentId: string, trendDays: number) => void;
  onOpenActive: (experimentId: string) => void;
  onOpenApprovals: (focusApprovalId?: string) => void;
  onOpenAttention: () => void;
  onOpenSnapshots: (snapshotDate: string, experimentId?: string) => void;
  onOpenActiveList: () => void;
  onOpenScoreProduct: () => void;
}>) {
  render(
    <Overview
      onOpenTrend={handlers.onOpenTrend ?? vi.fn()}
      onOpenActive={handlers.onOpenActive ?? vi.fn()}
      onOpenApprovals={handlers.onOpenApprovals ?? vi.fn()}
      onOpenAttention={handlers.onOpenAttention ?? vi.fn()}
      onOpenSnapshots={handlers.onOpenSnapshots ?? vi.fn()}
      onOpenActiveList={handlers.onOpenActiveList}
      onOpenScoreProduct={handlers.onOpenScoreProduct}
    />,
  );
  await waitFor(() => {
    expect(document.querySelector(".loading-row")).toBeNull();
    expect(screen.queryByText(/API error:/)).toBeNull();
  });
}

describe("Overview navigation wiring", () => {
  beforeEach(() => {
    vi.mocked(fetchDailyReport).mockReset();
    vi.mocked(fetchPendingApprovals).mockReset();
    vi.mocked(fetchOperatorHealthPanel).mockReset();
    vi.mocked(fetchOperatorReadiness).mockReset();
    vi.mocked(fetchExperimentTrendSummary).mockReset();
  });

  it("opens snapshots from header button with selected date", async () => {
    mockOverviewData({});
    const onOpenSnapshots = vi.fn();
    await renderOverview({ onOpenSnapshots });

    fireEvent.click(screen.getByRole("button", { name: "Snapshots" }));
    expect(onOpenSnapshots).toHaveBeenCalledWith("2026-06-23");
  });

  it("opens approval queue from pending banner with first approval id", async () => {
    mockOverviewData({
      pending: [
        {
          approval_id: "ap-1",
          action: "pause_ads",
          risk_level: "medium",
          status: "pending",
          summary: "Pause ads on Widget",
          expected_cost: 0,
          rollback_plan: "Resume",
          reason: "CAC high",
        },
      ],
    });
    const onOpenApprovals = vi.fn();
    await renderOverview({ onOpenApprovals });

    fireEvent.click(screen.getByRole("button", { name: /pending approval.*open queue/i }));
    expect(onOpenApprovals).toHaveBeenCalledWith("ap-1");
  });

  it("opens attention filter from trend header link", async () => {
    mockOverviewData({});
    const onOpenAttention = vi.fn();
    await renderOverview({ onOpenAttention });

    fireEvent.click(screen.getByRole("button", { name: /1 need attention/i }));
    expect(onOpenAttention).toHaveBeenCalledOnce();
  });

  it("opens trend chart and experiment details from trend row", async () => {
    mockOverviewData({});
    const onOpenTrend = vi.fn();
    const onOpenActive = vi.fn();
    await renderOverview({ onOpenTrend, onOpenActive });

    fireEvent.click(screen.getByRole("button", { name: "Chart" }));
    expect(onOpenTrend).toHaveBeenCalledWith("exp-trend", 14);

    fireEvent.click(screen.getByRole("button", { name: "Details" }));
    expect(onOpenActive).toHaveBeenCalledWith("exp-trend");
  });

  it("opens snapshot recorder for stale trend row", async () => {
    mockOverviewData({});
    const onOpenSnapshots = vi.fn();
    await renderOverview({ onOpenSnapshots });

    fireEvent.click(screen.getByRole("button", { name: "Record" }));
    expect(onOpenSnapshots).toHaveBeenCalledWith("2026-06-23", "exp-trend");
  });

  it("shows no-report empty state actions when daily report has no metrics", async () => {
    mockOverviewData({ report: null });
    const onOpenSnapshots = vi.fn();
    const onOpenScoreProduct = vi.fn();
    await renderOverview({ onOpenSnapshots, onOpenScoreProduct });

    fireEvent.click(screen.getByRole("button", { name: "Record a snapshot for 2026-06-23" }));
    expect(onOpenSnapshots).toHaveBeenCalledWith("2026-06-23");

    fireEvent.click(screen.getByRole("button", { name: "Score a product" }));
    expect(onOpenScoreProduct).toHaveBeenCalledOnce();
  });
});
