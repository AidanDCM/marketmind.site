import { describe, it, expect } from "vitest";
import {
  shouldLinkAddToCartToExperiments,
  shouldLinkRefundRateToExperiments,
} from "./overviewReportSecondaryMetrics";

const base = {
  date: "2026-06-23",
  revenue: 0,
  orders: 0,
  ad_spend: 50,
  refund_count: 0,
  contribution_profit: -50,
  cac: 0,
  conversion_rate: 0,
  add_to_cart_rate: 0.02,
  refund_rate: 0.04,
};

describe("overviewReportSecondaryMetrics", () => {
  it("links refund rate when at or above elevated threshold", () => {
    expect(shouldLinkRefundRateToExperiments({ ...base, refund_rate: 0.05 })).toBe(true);
    expect(shouldLinkRefundRateToExperiments({ ...base, refund_rate: 0.04 })).toBe(false);
  });

  it("links add-to-cart when spend with zero orders and rate below floor", () => {
    expect(shouldLinkAddToCartToExperiments(base)).toBe(true);
    expect(
      shouldLinkAddToCartToExperiments({ ...base, add_to_cart_rate: 0.03 }),
    ).toBe(false);
    expect(
      shouldLinkAddToCartToExperiments({ ...base, orders: 1 }),
    ).toBe(false);
    expect(
      shouldLinkAddToCartToExperiments({ ...base, ad_spend: 0 }),
    ).toBe(false);
  });
});
