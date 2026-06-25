import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { OverviewTrendEmptyState } from "./OverviewTrendEmptyState";

describe("OverviewTrendEmptyState", () => {
  it("opens active list from attention-only empty state", () => {
    const onOpenActiveList = vi.fn();
    render(
      <OverviewTrendEmptyState
        asOf="2026-06-23"
        attentionOnly
        onOpenActiveList={onOpenActiveList}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "View all experiments" }));
    expect(onOpenActiveList).toHaveBeenCalledOnce();
  });

  it("hides link when not in attention-only mode", () => {
    render(
      <OverviewTrendEmptyState
        asOf="2026-06-23"
        attentionOnly={false}
        onOpenActiveList={() => {}}
      />,
    );
    expect(screen.queryByRole("button", { name: "View all experiments" })).toBeNull();
  });

  it("hides link without handler", () => {
    render(
      <OverviewTrendEmptyState asOf="2026-06-23" attentionOnly />,
    );
    expect(screen.queryByRole("button", { name: "View all experiments" })).toBeNull();
  });
});
