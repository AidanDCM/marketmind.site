import { describe, it, expect } from "vitest";
import {
  buildExperimentProductLookup,
  parseDailyReportProductPrefix,
  resolveExperimentIdForReportLine,
  resolveDailyReportLineAction,
  isScaleApprovalRecommendation,
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
});
