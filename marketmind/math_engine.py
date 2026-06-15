"""Unit economics engine for MarketMind Autopilot."""

from __future__ import annotations

from .rules import (
    HIGH_NON_AD_COST_SHARE,
    HIGH_SHIPPING_SHARE,
    SAFE_CAC_HIGH_MULTIPLIER,
    SAFE_CAC_LOW_MULTIPLIER,
    margin_status,
    round_money,
)
from .schemas import ProductCostInput, RecommendedAction, UnitEconomicsResult


def calculate_unit_economics(product: ProductCostInput) -> UnitEconomicsResult:
    """Calculate first-order economics for a product or bundle.

    The engine does not call external APIs and does not approve spending. It only
    returns a structured recommendation based on supplied numbers.
    """

    total_non_ad_cost = (
        product.product_cost
        + product.packaging_cost
        + product.shipping_cost
        + product.platform_fee
        + product.payment_fee
        + product.refund_allowance
        + product.software_allocation
    )
    gross_profit_before_ads = product.sale_price - total_non_ad_cost
    break_even_cac = gross_profit_before_ads
    safe_cac_low = max(0.0, break_even_cac * SAFE_CAC_LOW_MULTIPLIER)
    safe_cac_high = max(0.0, break_even_cac * SAFE_CAC_HIGH_MULTIPLIER)
    estimated_contribution_profit = gross_profit_before_ads - product.estimated_cac
    gross_margin_before_ads = gross_profit_before_ads / product.sale_price
    contribution_margin_after_ads = estimated_contribution_profit / product.sale_price

    risks = _detect_risks(
        product=product,
        total_non_ad_cost=total_non_ad_cost,
        gross_profit_before_ads=gross_profit_before_ads,
        gross_margin_before_ads=gross_margin_before_ads,
        estimated_contribution_profit=estimated_contribution_profit,
        safe_cac_high=safe_cac_high,
    )

    status = margin_status(gross_margin_before_ads, contribution_margin_after_ads)
    action = _recommend_action(
        gross_profit_before_ads=gross_profit_before_ads,
        gross_margin_before_ads=gross_margin_before_ads,
        estimated_cac=product.estimated_cac,
        estimated_contribution_profit=estimated_contribution_profit,
        safe_cac_high=safe_cac_high,
        risks=risks,
    )
    reason_summary = _reason_summary(action, risks, estimated_contribution_profit)

    return UnitEconomicsResult(
        product_name=product.product_name,
        sale_price=round_money(product.sale_price),
        total_non_ad_cost=round_money(total_non_ad_cost),
        gross_profit_before_ads=round_money(gross_profit_before_ads),
        break_even_cac=round_money(break_even_cac),
        safe_cac_low=round_money(safe_cac_low),
        safe_cac_high=round_money(safe_cac_high),
        estimated_cac=round_money(product.estimated_cac),
        estimated_contribution_profit=round_money(estimated_contribution_profit),
        gross_margin_before_ads=round(gross_margin_before_ads, 4),
        contribution_margin_after_ads=round(contribution_margin_after_ads, 4),
        margin_status=status,
        recommended_action=action,
        risks=tuple(risks),
        reason_summary=reason_summary,
    )


def _detect_risks(
    *,
    product: ProductCostInput,
    total_non_ad_cost: float,
    gross_profit_before_ads: float,
    gross_margin_before_ads: float,
    estimated_contribution_profit: float,
    safe_cac_high: float,
) -> list[str]:
    risks: list[str] = []

    if gross_profit_before_ads <= 0:
        risks.append("non_ad_costs_exceed_sale_price")

    if estimated_contribution_profit < 0:
        risks.append("estimated_cac_makes_offer_unprofitable")

    if gross_margin_before_ads < 0.25:
        risks.append("gross_margin_too_thin")

    if product.shipping_cost / product.sale_price > HIGH_SHIPPING_SHARE:
        risks.append("shipping_cost_too_high")

    if total_non_ad_cost / product.sale_price > HIGH_NON_AD_COST_SHARE:
        risks.append("non_ad_costs_too_high")

    if product.estimated_cac > safe_cac_high and gross_profit_before_ads > 0:
        risks.append("estimated_cac_above_safe_range")

    return risks


def _recommend_action(
    *,
    gross_profit_before_ads: float,
    gross_margin_before_ads: float,
    estimated_cac: float,
    estimated_contribution_profit: float,
    safe_cac_high: float,
    risks: list[str],
) -> RecommendedAction:
    if gross_profit_before_ads <= 0:
        return RecommendedAction.REJECT

    if gross_margin_before_ads < 0.25:
        return RecommendedAction.REVISE_OFFER

    if estimated_cac == 0:
        if gross_margin_before_ads >= 0.40:
            return RecommendedAction.ORGANIC_ONLY_TEST
        return RecommendedAction.REVISE_OFFER

    if estimated_contribution_profit < 0:
        return RecommendedAction.PAUSE_ADS

    if estimated_cac <= safe_cac_high and gross_margin_before_ads >= 0.40:
        return RecommendedAction.PAID_TEST_REQUIRES_APPROVAL

    if "shipping_cost_too_high" in risks or "non_ad_costs_too_high" in risks:
        return RecommendedAction.REVISE_OFFER

    return RecommendedAction.CONTINUE_TEST


def _reason_summary(
    action: RecommendedAction, risks: list[str], estimated_contribution_profit: float
) -> str:
    if action == RecommendedAction.REJECT:
        return "Reject: non-ad costs exceed or consume the sale price before marketing."
    if action == RecommendedAction.REVISE_OFFER:
        return "Revise offer: margin or cost structure is too weak for safe scaling."
    if action == RecommendedAction.PAUSE_ADS:
        return "Pause ads: estimated CAC makes this offer unprofitable."
    if action == RecommendedAction.ORGANIC_ONLY_TEST:
        return "Organic-only test: math can work, but no paid acquisition estimate is approved yet."
    if action == RecommendedAction.PAID_TEST_REQUIRES_APPROVAL:
        return f"Paid test can be considered with approval; estimated contribution profit is {estimated_contribution_profit:.2f}."
    if risks:
        return "Continue carefully: economics are not immediately fatal, but risks need review."
    return "Continue: economics appear acceptable under current assumptions."
