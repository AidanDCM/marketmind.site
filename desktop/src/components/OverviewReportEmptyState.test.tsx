import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { OverviewReportEmptyState } from "./OverviewReportEmptyState";

describe("OverviewReportEmptyState", () => {
  it("opens snapshot recorder for the selected date", () => {
    const onOpenSnapshots = vi.fn();
    render(
      <OverviewReportEmptyState
        date="2026-06-23"
        onOpenSnapshots={onOpenSnapshots}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Record a snapshot for 2026-06-23" }));
    expect(onOpenSnapshots).toHaveBeenCalledWith("2026-06-23");
  });

  it("opens score product from empty report state", () => {
    const onOpenScoreProduct = vi.fn();
    render(
      <OverviewReportEmptyState
        date="2026-06-23"
        onOpenSnapshots={() => {}}
        onOpenScoreProduct={onOpenScoreProduct}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Score a product" }));
    expect(onOpenScoreProduct).toHaveBeenCalledOnce();
  });

  it("hides score product without handler", () => {
    render(
      <OverviewReportEmptyState date="2026-06-23" onOpenSnapshots={() => {}} />,
    );
    expect(screen.queryByRole("button", { name: "Score a product" })).toBeNull();
  });
});
