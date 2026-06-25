import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { OperatorMessageListItem } from "./OperatorMessageListItem";

describe("OperatorMessageListItem", () => {
  it("links missing snapshot warnings to snapshot recorder", () => {
    const onOpenSnapshots = vi.fn();
    render(
      <ul>
        <OperatorMessageListItem
          text="2 active experiment(s) missing snapshot for 2026-06-23: exp-a, exp-b"
          muted
          onOpenSnapshots={onOpenSnapshots}
        />
      </ul>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Record snapshot" }));
    expect(onOpenSnapshots).toHaveBeenCalledWith("2026-06-23", "exp-a");
  });

  it("links pending approval blockers to the queue", () => {
    const onOpenApprovals = vi.fn();
    render(
      <ul>
        <OperatorMessageListItem
          text="1 pending approval(s) have not been reviewed"
          onOpenApprovals={onOpenApprovals}
        />
      </ul>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Open queue" }));
    expect(onOpenApprovals).toHaveBeenCalledOnce();
  });

  it("links integration live-write warnings to Live Data", () => {
    const onOpenLiveData = vi.fn();
    render(
      <ul>
        <OperatorMessageListItem
          text="MARKETMIND_ENABLE_LIVE_WRITES=true but Gmail is not live-ready"
          muted
          onOpenLiveData={onOpenLiveData}
        />
      </ul>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Check Live Data" }));
    expect(onOpenLiveData).toHaveBeenCalledOnce();
  });

  it("links experiment ruling blockers to experiment details", () => {
    const onOpenActive = vi.fn();
    render(
      <ul>
        <OperatorMessageListItem
          text="Experiment 'exp-kill' ruling is 'kill' — action required"
          onOpenActive={onOpenActive}
        />
      </ul>,
    );
    fireEvent.click(screen.getByRole("button", { name: "View experiment" }));
    expect(onOpenActive).toHaveBeenCalledWith("exp-kill");
  });
});
