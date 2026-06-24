import type { DailyMetrics } from "../api/client";

/** Matches Overview metric-down styling for refund rate. */
export const REFUND_RATE_ELEVATED = 0.05;

/** Mirrors `KILL_ATC_RATE` in `marketmind/rules.py`. */
export const ADD_TO_CART_FLOOR = 0.03;

export function shouldLinkRefundRateToExperiments(metrics: DailyMetrics): boolean {
  return metrics.refund_rate >= REFUND_RATE_ELEVATED;
}

export function shouldLinkAddToCartToExperiments(metrics: DailyMetrics): boolean {
  return (
    metrics.ad_spend > 0
    && metrics.orders === 0
    && metrics.add_to_cart_rate < ADD_TO_CART_FLOOR
  );
}

/** Spend with zero orders — matches daily report zero-order spend risk context. */
export function shouldLinkConversionToExperiments(metrics: DailyMetrics): boolean {
  return metrics.ad_spend > 0 && metrics.orders === 0;
}

export function secondaryMetricsActiveListTitle(
  kind: "contribution" | "refund" | "atc" | "conversion",
): string {
  switch (kind) {
    case "contribution":
      return "Open Active Experiments";
    case "refund":
      return "Open Active Experiments — review refund rate";
    case "atc":
      return "Open Active Experiments — review add-to-cart";
    case "conversion":
      return "Open Active Experiments — review conversion";
  }
}
