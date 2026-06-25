import { describe, it, expect } from "vitest";
import {
  preflightSummaryActions,
  preflightSummaryActionLabel,
} from "./preflightSummaryActions";

describe("preflightSummaryActions", () => {
  it("returns no actions when safe to operate", () => {
    expect(
      preflightSummaryActions({
        safeToOperate: true,
        pendingApprovals: 2,
        experimentsNeedingAttention: 1,
      }),
    ).toEqual([]);
  });

  it("returns queue and attention actions when blocked", () => {
    expect(
      preflightSummaryActions({
        safeToOperate: false,
        pendingApprovals: 2,
        experimentsNeedingAttention: 1,
      }),
    ).toEqual(["approvals", "attention"]);
    expect(preflightSummaryActionLabel("approvals")).toBe("Open queue");
    expect(preflightSummaryActionLabel("attention")).toBe("Show attention");
  });

  it("returns only queue when pending approvals block operate", () => {
    expect(
      preflightSummaryActions({
        safeToOperate: false,
        pendingApprovals: 1,
        experimentsNeedingAttention: 0,
      }),
    ).toEqual(["approvals"]);
  });

  it("returns only attention when experiments need action", () => {
    expect(
      preflightSummaryActions({
        safeToOperate: false,
        pendingApprovals: 0,
        experimentsNeedingAttention: 2,
      }),
    ).toEqual(["attention"]);
  });
});
