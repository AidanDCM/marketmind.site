import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { OverviewReportSecondaryMetrics } from "./OverviewReportSecondaryMetrics";

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

describe("OverviewReportSecondaryMetrics", () => {
  it("opens active experiments from contribution profit metric", () => {
    const onOpenActiveList = vi.fn();
    render(
      <OverviewReportSecondaryMetrics
        metrics={metrics}
        onOpenActiveList={onOpenActiveList}
      />,
    );
    fireEvent.click(screen.getByTitle("Open Active Experiments"));
    expect(onOpenActiveList).toHaveBeenCalledOnce();
  });
});
