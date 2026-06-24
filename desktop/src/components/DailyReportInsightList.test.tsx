import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DailyReportInsightList } from "./DailyReportInsightList";

describe("DailyReportInsightList", () => {
  it("links product-specific risks to experiment details", () => {
    const onOpenActive = vi.fn();
    render(
      <DailyReportInsightList
        title="Risks"
        bulletClass="risk"
        items={["Silicone Mat: CAC $42.00 above break-even $30.00."]}
        experiments={[{ experiment_id: "exp-1", product_name: "Silicone Mat" }]}
        onOpenActive={onOpenActive}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "View experiment" }));
    expect(onOpenActive).toHaveBeenCalledWith("exp-1");
  });

  it("renders generic risks without a link", () => {
    render(
      <DailyReportInsightList
        title="Risks"
        bulletClass="risk"
        items={["Spend with zero orders today — check targeting and offer."]}
        experiments={[]}
      />,
    );
    expect(screen.queryByRole("button", { name: "View experiment" })).toBeNull();
  });

  it("opens approval queue for scale recommendations", () => {
    const onOpenApprovals = vi.fn();
    render(
      <DailyReportInsightList
        title="Recommendations"
        bulletClass="rec"
        items={[
          "Silicone Mat: hitting scale criteria (CAC $24.00, 8 orders) — submit scale request for approval.",
        ]}
        experiments={[{ experiment_id: "exp-1", product_name: "Silicone Mat" }]}
        onOpenApprovals={onOpenApprovals}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Open queue" }));
    expect(onOpenApprovals).toHaveBeenCalledOnce();
  });
});
