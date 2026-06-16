"""Kill/scale experiment rule engine for MarketMind Autopilot (Slice 4).

Applies the PNL_MODEL kill and scale rules against live experiment performance.
Pure computation only: no external API calls, no spending, no side effects.

The engine is deliberately pessimistic. It prefers killing a weak experiment
over continuing to burn budget on optimistic signals.
"""

from __future__ import annotations

from .rules import (
    KILL_ATC_RATE,
    KILL_CONSECUTIVE_LOSING_PERIODS,
    KILL_REFUND_RATE,
    KILL_SHIPPING_OVERRUN,
    KILL_VISITS_WITHOUT_SALE,
    SCALE_MAX_CAC_FACTOR,
    SCALE_MIN_CONVERSION_RATE,
    SCALE_MIN_ORDERS,
)
from .schemas import (
    ExperimentRuling,
    ExperimentRulingResult,
    ExperimentSnapshot,
)


def evaluate_experiment(snapshot: ExperimentSnapshot) -> ExperimentRulingResult:
    """Evaluate a live experiment snapshot and return a kill/scale/continue ruling.

    Rule priority (highest to lowest):
    1. Budget not set -> block any ads, refuse to rule on scale.
    2. Kill triggers -> immediately stop.
    3. Pause triggers -> stop ads but keep the page live.
    4. Revise triggers -> math is wrong, fix the offer.
    5. Scale -> only when every positive condition is met.
    6. Continue -> nothing alarming, keep watching.
    """

    risks: list[str] = []

    # --- detect all risk signals first ------------------------------------

    if snapshot.budget_cap <= 0 and snapshot.total_ad_spend > 0:
        risks.append("spend_without_approved_budget")

    if snapshot.consecutive_losing_periods >= KILL_CONSECUTIVE_LOSING_PERIODS:
        risks.append("cac_above_break_even_multiple_periods")

    has_meaningful_traffic = snapshot.qualified_visits >= 100

    if (
        has_meaningful_traffic
        and snapshot.qualified_visits >= KILL_VISITS_WITHOUT_SALE
        and snapshot.orders == 0
    ):
        risks.append("no_sales_after_qualified_traffic")

    if (
        has_meaningful_traffic
        and snapshot.add_to_cart_rate < KILL_ATC_RATE
        and snapshot.qualified_visits >= 200
    ):
        risks.append("add_to_cart_rate_too_low")

    if snapshot.orders > 0 and snapshot.refund_rate > KILL_REFUND_RATE:
        risks.append("refund_rate_too_high")

    if snapshot.shipping_overrun > KILL_SHIPPING_OVERRUN:
        risks.append("shipping_cost_overrun")

    if snapshot.orders > 0 and snapshot.actual_cac > snapshot.break_even_cac:
        risks.append("cac_above_break_even")

    has_low_conversion = (
        has_meaningful_traffic
        and snapshot.orders > 0
        and snapshot.conversion_rate < SCALE_MIN_CONVERSION_RATE
    )
    if has_low_conversion:
        risks.append("conversion_rate_too_low")

    # --- apply ruling in priority order ----------------------------------

    _HARD_KILL = {
        "cac_above_break_even_multiple_periods",
        "no_sales_after_qualified_traffic",
        "refund_rate_too_high",
    }
    if _HARD_KILL & set(risks):
        return ExperimentRulingResult(
            experiment_id=snapshot.experiment_id,
            product_name=snapshot.product_name,
            ruling=ExperimentRuling.KILL,
            risks=tuple(risks),
            reason_summary=_kill_reason(risks),
            requires_approval=False,
        )

    if "spend_without_approved_budget" in risks:
        return ExperimentRulingResult(
            experiment_id=snapshot.experiment_id,
            product_name=snapshot.product_name,
            ruling=ExperimentRuling.PAUSE_ADS,
            risks=tuple(risks),
            reason_summary="Pause ads: no approved budget has been set (APPROVAL_POLICY.md).",
            requires_approval=False,
        )

    if "cac_above_break_even" in risks:
        return ExperimentRulingResult(
            experiment_id=snapshot.experiment_id,
            product_name=snapshot.product_name,
            ruling=ExperimentRuling.PAUSE_ADS,
            risks=tuple(risks),
            reason_summary=(
                f"Pause ads: actual CAC ({snapshot.actual_cac:.2f}) is above "
                f"break-even ({snapshot.break_even_cac:.2f})."
            ),
            requires_approval=False,
        )

    if {"add_to_cart_rate_too_low", "shipping_cost_overrun"} & set(risks):
        return ExperimentRulingResult(
            experiment_id=snapshot.experiment_id,
            product_name=snapshot.product_name,
            ruling=ExperimentRuling.REVISE_OFFER,
            risks=tuple(risks),
            reason_summary="Revise offer: funnel or cost structure is broken.",
            requires_approval=False,
        )

    # Scale: every positive condition must be true simultaneously.
    safe_cac_max = snapshot.break_even_cac * SCALE_MAX_CAC_FACTOR
    cac_is_safe = snapshot.orders > 0 and snapshot.actual_cac <= safe_cac_max
    enough_orders = snapshot.orders >= SCALE_MIN_ORDERS
    conversion_ok = (
        snapshot.orders > 0
        and snapshot.conversion_rate >= SCALE_MIN_CONVERSION_RATE
    )
    refund_ok = snapshot.orders == 0 or snapshot.refund_rate <= KILL_REFUND_RATE
    shipping_ok = snapshot.shipping_overrun <= KILL_SHIPPING_OVERRUN

    if cac_is_safe and enough_orders and conversion_ok and refund_ok and shipping_ok:
        return ExperimentRulingResult(
            experiment_id=snapshot.experiment_id,
            product_name=snapshot.product_name,
            ruling=ExperimentRuling.SCALE_REQUIRES_APPROVAL,
            risks=tuple(risks),
            reason_summary=(
                f"Scale candidate: {snapshot.orders} orders, "
                f"CAC {snapshot.actual_cac:.2f} vs safe-max {safe_cac_max:.2f}. "
                "Requires approval before budget increase."
            ),
            requires_approval=True,
        )

    return ExperimentRulingResult(
        experiment_id=snapshot.experiment_id,
        product_name=snapshot.product_name,
        ruling=ExperimentRuling.CONTINUE,
        risks=tuple(risks),
        reason_summary=_continue_reason(snapshot, risks),
        requires_approval=False,
    )


def _kill_reason(risks: list[str]) -> str:
    if "cac_above_break_even_multiple_periods" in risks:
        return (
            f"Kill: CAC has been above break-even for "
            f"{KILL_CONSECUTIVE_LOSING_PERIODS}+ consecutive periods."
        )
    if "no_sales_after_qualified_traffic" in risks:
        return f"Kill: no sales after {KILL_VISITS_WITHOUT_SALE} qualified visits."
    if "refund_rate_too_high" in risks:
        return f"Kill: refund rate exceeds {KILL_REFUND_RATE:.0%} threshold."
    return "Kill: multiple hard failure signals reached simultaneously."


def _continue_reason(snapshot: ExperimentSnapshot, risks: list[str]) -> str:
    if not risks:
        if snapshot.orders == 0:
            return "Continue: early stage — not enough data to rule yet."
        return "Continue: performance is within acceptable bounds."
    return f"Continue with caution: {len(risks)} risk signal(s) present but no hard kill trigger."
