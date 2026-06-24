import { describe, it, expect } from "vitest";
import { pendingApprovalBannerText } from "./approvalDisplay";

describe("pendingApprovalBannerText", () => {
  it("returns empty string when no pending approvals", () => {
    expect(pendingApprovalBannerText([])).toBe("");
  });

  it("includes count and first summary example", () => {
    const text = pendingApprovalBannerText([
      {
        approval_id: "a1",
        action: "stripe_charge",
        risk_level: "high",
        status: "pending",
        summary: "Scale ad spend for kit_001",
        expected_cost: 100,
        rollback_plan: "pause",
        reason: "test",
      },
    ]);
    expect(text).toContain("1 pending approval");
    expect(text).toContain("Scale ad spend for kit_001");
    expect(text).toContain("open queue");
  });

  it("falls back to action when summary is blank", () => {
    const text = pendingApprovalBannerText([
      {
        approval_id: "a1",
        action: "shopify_product_create",
        risk_level: "high",
        status: "pending",
        summary: "",
        expected_cost: 0,
        rollback_plan: "",
        reason: "",
      },
    ]);
    expect(text).toContain("shopify_product_create");
  });
});
