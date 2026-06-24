import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { OperatorReadinessBanner } from "./OperatorReadinessBanner";
import type { OperatorReadiness } from "../api/client";

const base: OperatorReadiness = {
  ready: true,
  blockers: [],
  warnings: [],
  safe_to_operate: true,
  gmail: { mode: "simulate", live_ready: false },
  commerce: {
    stripe: { configured: false, live_ready: false },
    shopify: { configured: false, live_ready: false },
  },
  snapshot_gaps: {
    snapshot_date: "2026-06-23",
    active_count: 0,
    missing_count: 0,
    missing: [],
    all_recorded: false,
  },
};

describe("OperatorReadinessBanner", () => {
  it("renders ready state", () => {
    render(<OperatorReadinessBanner readiness={base} />);
    expect(screen.getByText(/Operator readiness: ready/)).toBeInTheDocument();
    expect(screen.getByText(/Gmail simulate/)).toBeInTheDocument();
  });

  it("renders blockers when not ready", () => {
    render(
      <OperatorReadinessBanner
        readiness={{
          ...base,
          ready: false,
          blockers: ["2 pending approval(s) have not been reviewed"],
        }}
      />,
    );
    expect(screen.getByText(/not ready/)).toBeInTheDocument();
    expect(screen.getByText(/pending approval/)).toBeInTheDocument();
  });

  it("links pending approval blockers to the queue", () => {
    const onOpenApprovals = vi.fn();
    render(
      <OperatorReadinessBanner
        readiness={{
          ...base,
          ready: false,
          blockers: ["2 pending approval(s) have not been reviewed"],
        }}
        onOpenApprovals={onOpenApprovals}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Open queue" }));
    expect(onOpenApprovals).toHaveBeenCalledOnce();
  });

  it("links experiment ruling blockers to experiment details", () => {
    const onOpenActive = vi.fn();
    render(
      <OperatorReadinessBanner
        readiness={{
          ...base,
          ready: false,
          blockers: ["Experiment 'exp-7' ruling is 'kill' — action required"],
        }}
        onOpenActive={onOpenActive}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "View experiment" }));
    expect(onOpenActive).toHaveBeenCalledWith("exp-7");
  });

  it("links missing snapshot warnings to snapshot recorder", () => {
    const onOpenSnapshots = vi.fn();
    render(
      <OperatorReadinessBanner
        readiness={{
          ...base,
          warnings: [
            "2 active experiment(s) missing snapshot for 2026-06-23: exp-a, exp-b",
          ],
        }}
        onOpenSnapshots={onOpenSnapshots}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Record snapshot" }));
    expect(onOpenSnapshots).toHaveBeenCalledWith("2026-06-23", "exp-a");
  });

  it("links integration warnings to Live Data", () => {
    const onOpenLiveData = vi.fn();
    render(
      <OperatorReadinessBanner
        readiness={{
          ...base,
          warnings: ["Gmail live mode enabled but GMAIL_CLIENT_SECRET is missing"],
        }}
        onOpenLiveData={onOpenLiveData}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Check Live Data" }));
    expect(onOpenLiveData).toHaveBeenCalledOnce();
  });
});
