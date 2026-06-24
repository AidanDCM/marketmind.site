import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { OverviewReportPrimaryMetrics } from "./OverviewReportPrimaryMetrics";

const metrics = {
  date: "2026-06-23",
  revenue: 2400,
  orders: 12,
  ad_spend: 800,
  refund_count: 0,
  contribution_profit: 400,
  cac: 67,
  conversion_rate: 0.03,
  add_to_cart_rate: 0.12,
  refund_rate: 0.02,
};

describe("OverviewReportPrimaryMetrics", () => {
  it("opens import history from ad spend metric", () => {
    const onOpenImportHistory = vi.fn();
    render(
      <OverviewReportPrimaryMetrics
        metrics={metrics}
        date="2026-06-23"
        onOpenImportHistory={onOpenImportHistory}
      />,
    );
    fireEvent.click(screen.getByTitle("Open Import History"));
    expect(onOpenImportHistory).toHaveBeenCalledOnce();
  });

  it("opens live data from orders metric", () => {
    const onOpenLiveData = vi.fn();
    render(
      <OverviewReportPrimaryMetrics
        metrics={metrics}
        date="2026-06-23"
        onOpenLiveData={onOpenLiveData}
      />,
    );
    fireEvent.click(screen.getByTitle("Open Live Data"));
    expect(onOpenLiveData).toHaveBeenCalledOnce();
  });
});
