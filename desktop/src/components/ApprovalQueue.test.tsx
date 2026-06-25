import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { ApprovalQueue } from "./ApprovalQueue";
import type { ApprovalRecord } from "../api/client";

vi.mock("../api/client", () => ({
  fetchApprovals: vi.fn(),
  approveRecord: vi.fn(),
  denyRecord: vi.fn(),
  executeApproved: vi.fn(),
}));

import { fetchApprovals, executeApproved } from "../api/client";

const pendingRec: ApprovalRecord = {
  approval_id: "apr-pending",
  action: "scale_campaign",
  risk_level: "high",
  status: "pending",
  summary: "Scale Interior Kit ads",
  expected_cost: 200,
  rollback_plan: "Pause campaign",
  reason: "CAC within target",
};

const approvedRec: ApprovalRecord = {
  ...pendingRec,
  approval_id: "apr-approved",
  status: "approved",
  summary: "Approved scale request",
};

async function renderQueue(records: ApprovalRecord[]) {
  vi.mocked(fetchApprovals).mockResolvedValue(records);
  render(<ApprovalQueue />);
  await waitFor(() => {
    expect(document.querySelector(".loading-row")).toBeNull();
  });
}

describe("ApprovalQueue gate UI", () => {
  beforeEach(() => {
    vi.mocked(fetchApprovals).mockReset();
    vi.mocked(executeApproved).mockReset();
  });

  it("shows approve and deny for pending records, not execute", async () => {
    await renderQueue([pendingRec]);
    const card = screen.getByText("Scale Interior Kit ads").closest(".approval-card")!;
    fireEvent.click(within(card as HTMLElement).getByText("Scale Interior Kit ads"));

    expect(within(card as HTMLElement).getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(within(card as HTMLElement).getByRole("button", { name: "Deny" })).toBeInTheDocument();
    expect(within(card as HTMLElement).queryByRole("button", { name: "Execute (dry-run)" })).toBeNull();
  });

  it("executes approved records with dry_run forced true", async () => {
    vi.mocked(executeApproved).mockResolvedValue({
      approval_id: "apr-approved",
      action: "scale_campaign",
      executed: true,
      dry_run: true,
      reason: "",
      detail: { kind: "scale_campaign" },
    });
    await renderQueue([approvedRec]);
    const card = screen.getByText("Approved scale request").closest(".approval-card")!;
    fireEvent.click(within(card as HTMLElement).getByText("Approved scale request"));

    fireEvent.click(within(card as HTMLElement).getByRole("button", { name: "Execute (dry-run)" }));
    await waitFor(() => {
      expect(executeApproved).toHaveBeenCalledWith("apr-approved", true);
    });
  });

  it("shows no execute control for denied records", async () => {
    const deniedRec: ApprovalRecord = {
      ...pendingRec,
      approval_id: "apr-denied",
      status: "denied",
      summary: "Denied scale request",
    };
    await renderQueue([deniedRec]);
    const card = screen.getByText("Denied scale request").closest(".approval-card")!;
    fireEvent.click(within(card as HTMLElement).getByText("Denied scale request"));
    expect(within(card as HTMLElement).queryByRole("button", { name: "Execute (dry-run)" })).toBeNull();
    expect(within(card as HTMLElement).queryByRole("button", { name: "Approve" })).toBeNull();
  });

  it("shows no approve or execute controls for blocked records", async () => {
    const blockedRec: ApprovalRecord = {
      ...pendingRec,
      approval_id: "apr-blocked",
      status: "blocked",
      summary: "Blocked bypass attempt",
      action: "bypass_approval_gate",
    };
    await renderQueue([blockedRec]);
    const card = screen.getByText("Blocked bypass attempt").closest(".approval-card")!;
    fireEvent.click(within(card as HTMLElement).getByText("Blocked bypass attempt"));
    expect(within(card as HTMLElement).queryByRole("button", { name: "Approve" })).toBeNull();
    expect(within(card as HTMLElement).queryByRole("button", { name: "Deny" })).toBeNull();
    expect(within(card as HTMLElement).queryByRole("button", { name: "Execute (dry-run)" })).toBeNull();
  });
});
