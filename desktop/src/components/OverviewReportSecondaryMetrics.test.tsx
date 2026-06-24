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

  it("opens active experiments from elevated refund rate metric", () => {
    const onOpenActiveList = vi.fn();
    render(
      <OverviewReportSecondaryMetrics
        metrics={{ ...metrics, refund_rate: 0.06 }}
        onOpenActiveList={onOpenActiveList}
      />,
    );
    fireEvent.click(screen.getByTitle("Open Active Experiments — review refund rate"));
    expect(onOpenActiveList).toHaveBeenCalledOnce();
  });

  it("opens active experiments from low add-to-cart with spend and no orders", () => {
    const onOpenActiveList = vi.fn();
    render(
      <OverviewReportSecondaryMetrics
        metrics={{
          ...metrics,
          orders: 0,
          ad_spend: 120,
          add_to_cart_rate: 0.02,
          refund_rate: 0,
        }}
        onOpenActiveList={onOpenActiveList}
      />,
    );
    fireEvent.click(screen.getByTitle("Open Active Experiments — review add-to-cart"));
    expect(onOpenActiveList).toHaveBeenCalledOnce();
  });

  it("does not link refund rate when below elevated threshold", () => {
    render(
      <OverviewReportSecondaryMetrics metrics={metrics} onOpenActiveList={() => {}} />,
    );
    expect(
      screen.queryByTitle("Open Active Experiments — review refund rate"),
    ).toBeNull();
  });
});
