import { describe, it, expect } from "vitest";
import {
  buildExperimentProductLookup,
  parseDailyReportProductPrefix,
  resolveExperimentIdForReportLine,
  resolveDailyReportLineAction,
  isScaleApprovalRecommendation,
  isGenericPortfolioRisk,
  ZERO_ORDER_SPEND_RISK,
  resolveDailyReportLessonAction,
  dailyReportLessonActionLabel,
} from "./dailyReportNavigation";

describe("dailyReportNavigation", () => {
  const lookup = buildExperimentProductLookup([
    [{ experiment_id: "exp-1", product_name: "Silicone Mat" }],
  ]);

  it("parses product prefix from report lines", () => {
    expect(parseDailyReportProductPrefix("Silicone Mat: CAC $42.00 above break-even $30.00."))
      .toBe("Silicone Mat");
    expect(parseDailyReportProductPrefix("Spend with zero orders today")).toBeNull();
  });

  it("resolves experiment id by product name", () => {
    expect(
      resolveExperimentIdForReportLine(
        "Silicone Mat: hitting scale criteria (CAC $24.00, 8 orders) — submit scale request for approval.",
        lookup,
      ),
    ).toBe("exp-1");
  });

  it("returns undefined when product is unknown", () => {
    expect(
      resolveExperimentIdForReportLine("Unknown Product: CAC $50.00 above break-even $30.00.", lookup),
    ).toBeUndefined();
  });

  it("routes scale recommendations to the approval queue", () => {
    const line =
      "Silicone Mat: hitting scale criteria (CAC $24.00, 8 orders) — submit scale request for approval.";
    expect(isScaleApprovalRecommendation(line)).toBe(true);
    expect(resolveDailyReportLineAction(line, lookup)).toEqual({ kind: "approvals" });
  });

  it("routes product risks to experiment details", () => {
    expect(
      resolveDailyReportLineAction("Silicone Mat: CAC $42.00 above break-even $30.00.", lookup),
    ).toEqual({ kind: "experiment", experimentId: "exp-1" });
  });

  it("routes no-experiments recommendation to score product", () => {
    expect(
      resolveDailyReportLineAction(
        "No experiments active today. Pick a product candidate to test.",
        lookup,
      ),
    ).toEqual({ kind: "score" });
  });

  it("routes positive contribution recommendation to active experiments", () => {
    expect(
      resolveDailyReportLineAction(
        "Positive contribution today ($120.00). Review experiment rules before increasing budget.",
        lookup,
      ),
    ).toEqual({ kind: "activeList" });
  });

  it("routes generic portfolio risks to active experiments", () => {
    expect(isGenericPortfolioRisk(ZERO_ORDER_SPEND_RISK)).toBe(true);
    expect(
      resolveDailyReportLineAction(
        "Refund rate 12.0% exceeds kill threshold 10% — review product quality.",
        lookup,
      ),
    ).toEqual({ kind: "activeList" });
    expect(
      resolveDailyReportLineAction(
        "Add-to-cart rate 1.0% below floor 2% — creative or price needs revision.",
        lookup,
      ),
    ).toEqual({ kind: "activeList" });
  });

  it("routes pending approval lessons to the queue", () => {
    const action = resolveDailyReportLessonAction(
      "2 approval(s) pending — unblocking these may unlock next steps.",
    );
    expect(action).toEqual({ kind: "approvals" });
    expect(dailyReportLessonActionLabel(action!)).toBe("Open queue");
  });

  it("routes no-orders lessons to live data", () => {
    const action = resolveDailyReportLessonAction(
      "No orders: verify that the payment link / checkout is live and working.",
    );
    expect(action).toEqual({ kind: "live" });
    expect(dailyReportLessonActionLabel(action!)).toBe("Check Live Data");
  });

  it("routes past lessons to the lessons library", () => {
    const action = resolveDailyReportLessonAction("Past lesson: Pause ads when CAC spikes.");
    expect(action).toEqual({ kind: "lessons" });
    expect(dailyReportLessonActionLabel(action!)).toBe("View library");
  });

  it("routes low ROAS lessons to active experiments", () => {
    const action = resolveDailyReportLessonAction(
      "ROAS is 0.75 (below 1.0) — spending more than earning from ads.",
    );
    expect(action).toEqual({ kind: "activeList" });
  });
});
