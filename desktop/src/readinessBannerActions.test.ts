import { describe, it, expect } from "vitest";
import {
  parseReadinessBannerAction,
  readinessBannerActionLabel,
  GMAIL_LIVE_WARNING,
  STRIPE_LIVE_WARNING_PREFIX,
} from "./readinessBannerActions";

describe("readinessBannerActions", () => {
  it("maps pending approval blockers to the approval queue", () => {
    const action = parseReadinessBannerAction(
      "2 pending approval(s) have not been reviewed",
    );
    expect(action).toEqual({ kind: "approvals" });
    expect(readinessBannerActionLabel(action!)).toBe("Open queue");
  });

  it("maps experiment ruling blockers to experiment details", () => {
    const action = parseReadinessBannerAction(
      "Experiment 'exp-42' ruling is 'kill' — action required",
    );
    expect(action).toEqual({ kind: "active", experimentId: "exp-42" });
    expect(readinessBannerActionLabel(action!)).toBe("View experiment");
  });

  it("maps missing snapshot warnings to snapshot recorder", () => {
    const action = parseReadinessBannerAction(
      "3 active experiment(s) missing snapshot for 2026-06-23: exp-a, exp-b, exp-c",
    );
    expect(action).toEqual({
      kind: "snapshots",
      snapshotDate: "2026-06-23",
      experimentId: "exp-a",
    });
    expect(readinessBannerActionLabel(action!)).toBe("Record snapshot");
  });

  it("returns null for unrecognized messages", () => {
    expect(parseReadinessBannerAction("Gmail live mode enabled but secret missing")).toBeNull();
  });

  it("maps integration live-write warnings to Live Data", () => {
    const action = parseReadinessBannerAction(GMAIL_LIVE_WARNING);
    expect(action).toEqual({ kind: "live" });
    expect(readinessBannerActionLabel(action!)).toBe("Check Live Data");
  });

  it("maps Stripe live-write warnings to Live Data", () => {
    const action = parseReadinessBannerAction(
      `${STRIPE_LIVE_WARNING_PREFIX} (set STRIPE_API_KEY and MARKETMIND_STRIPE_DRY_RUN=false)`,
    );
    expect(action).toEqual({ kind: "live" });
    expect(readinessBannerActionLabel(action!)).toBe("Check Live Data");
  });
});
