"""Slice 8: Daily report generator.

Adapts the JsonlEventLedger pattern from Parts & Pieces
(AidanDCM/Parts-and-Pieces/parts/python/event_ledger/jsonl_event_ledger.py).
This module is pure computation: accepts Python objects in, returns DailyReport
out. No file I/O, no API calls. The caller hydrates snapshots from the ledger.

generate_daily_report() aggregates experiment snapshots for a date, identifies
risks and recommendations from the business rules in rules.py, and returns a
structured DailyReport the operator (or Codex dashboard) can act on.
"""

from __future__ import annotations

from .experiment_lifecycle_contract import (
    ATC_RISK_SUFFIX,
    LOW_ROAS_LESSON_MARKER,
    NO_EXPERIMENTS_RECOMMENDATION,
    NO_ORDERS_LESSON_PREFIX,
    PAST_LESSON_PREFIX,
    POSITIVE_CONTRIBUTION_PREFIX,
    REFUND_RISK_SUFFIX,
    ROAS_SCALE_LESSON_PHRASE,
    SCALE_APPROVAL_PHRASE,
    ZERO_ORDER_SPEND_RISK,
)
from .rules import KILL_ATC_RATE, KILL_REFUND_RATE, SCALE_MAX_CAC_FACTOR, SCALE_MIN_ORDERS
from .schemas import (
    ApprovalRecord,
    ApprovalStatus,
    DailyMetrics,
    DailyReport,
    ExperimentSnapshot,
)

# ---------------------------------------------------------------------------
# Metrics aggregation
# ---------------------------------------------------------------------------


def _aggregate_metrics(date: str, snapshots: list[ExperimentSnapshot]) -> DailyMetrics:
    if not snapshots:
        return DailyMetrics(date=date)

    total_revenue = sum(s.total_revenue for s in snapshots)
    total_orders = sum(s.orders for s in snapshots)
    total_ad_spend = sum(s.total_ad_spend for s in snapshots)
    total_refund_count = sum(s.refund_count for s in snapshots)
    total_visits = sum(s.qualified_visits for s in snapshots)
    total_atc = sum(s.add_to_cart_count for s in snapshots)

    contribution_profit = total_revenue - total_ad_spend
    cac = total_ad_spend / total_orders if total_orders > 0 else 0.0
    conversion_rate = total_orders / total_visits if total_visits > 0 else 0.0
    add_to_cart_rate = total_atc / total_visits if total_visits > 0 else 0.0
    refund_rate = total_refund_count / total_orders if total_orders > 0 else 0.0

    return DailyMetrics(
        date=date,
        revenue=round(total_revenue, 2),
        orders=total_orders,
        ad_spend=round(total_ad_spend, 2),
        refund_count=total_refund_count,
        contribution_profit=round(contribution_profit, 2),
        cac=round(cac, 2),
        conversion_rate=round(conversion_rate, 4),
        add_to_cart_rate=round(add_to_cart_rate, 4),
        refund_rate=round(refund_rate, 4),
    )


# ---------------------------------------------------------------------------
# Recommendation and risk derivation
# ---------------------------------------------------------------------------


def _derive_recommendations_and_risks(
    metrics: DailyMetrics,
    snapshots: list[ExperimentSnapshot],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    recommendations: list[str] = []
    risks: list[str] = []

    if not snapshots:
        recommendations.append(NO_EXPERIMENTS_RECOMMENDATION)
        return tuple(recommendations), tuple(risks)

    if metrics.orders == 0 and metrics.ad_spend > 0:
        risks.append(ZERO_ORDER_SPEND_RISK)

    if metrics.refund_rate > KILL_REFUND_RATE:
        risks.append(
            f"Refund rate {metrics.refund_rate:.1%} exceeds kill threshold "
            f"{KILL_REFUND_RATE:.0%}{REFUND_RISK_SUFFIX}"
        )

    if metrics.ad_spend > 0 and metrics.orders == 0 and metrics.add_to_cart_rate < KILL_ATC_RATE:
        risks.append(
            f"Add-to-cart rate {metrics.add_to_cart_rate:.1%} below floor "
            f"{KILL_ATC_RATE:.0%}{ATC_RISK_SUFFIX}"
        )

    for snap in snapshots:
        if snap.break_even_cac > 0 and snap.actual_cac > snap.break_even_cac:
            risks.append(
                f"{snap.product_name}: CAC ${snap.actual_cac:.2f} above "
                f"break-even ${snap.break_even_cac:.2f}."
            )
        elif (
            snap.break_even_cac > 0
            and snap.actual_cac <= snap.break_even_cac * SCALE_MAX_CAC_FACTOR
            and snap.orders >= SCALE_MIN_ORDERS
        ):
            recommendations.append(
                f"{snap.product_name}: hitting scale criteria "
                f"(CAC ${snap.actual_cac:.2f}, {snap.orders} orders) — "
                f"{SCALE_APPROVAL_PHRASE}"
            )

    if metrics.contribution_profit > 0 and metrics.orders > 0:
        recommendations.append(
            f"{POSITIVE_CONTRIBUTION_PREFIX} (${metrics.contribution_profit:.2f}). "
            "Review experiment rules before increasing budget."
        )

    return tuple(recommendations), tuple(risks)


# ---------------------------------------------------------------------------
# Lesson extraction (mirrors ledger replay: events → derived lessons)
# ---------------------------------------------------------------------------


def _derive_lessons(
    metrics: DailyMetrics,
    pending_approvals: list[ApprovalRecord],
    recent_mistakes: list[str] | None = None,
) -> tuple[str, ...]:
    lessons: list[str] = []

    if metrics.orders == 0:
        lessons.append(NO_ORDERS_LESSON_PREFIX)

    pending = [r for r in pending_approvals if r.status == ApprovalStatus.PENDING]
    if pending:
        lessons.append(
            f"{len(pending)} approval(s) pending — unblocking these may unlock next steps."
        )

    for mistake_lesson in recent_mistakes or []:
        lessons.append(f"{PAST_LESSON_PREFIX}{mistake_lesson}")

    if metrics.ad_spend > 0:
        roas = metrics.revenue / metrics.ad_spend
        if roas < 1.0:
            lessons.append(
                f"ROAS is {roas:.2f} {LOW_ROAS_LESSON_MARKER} — "
                "spending more than earning from ads."
            )
        elif roas >= 3.0:
            lessons.append(
                f"ROAS is {roas:.2f} — healthy signal; {ROAS_SCALE_LESSON_PHRASE}"
            )

    return tuple(lessons)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_daily_report(
    date: str,
    snapshots: list[ExperimentSnapshot],
    pending_approvals: list[ApprovalRecord] | None = None,
    recent_mistakes: list[str] | None = None,
) -> DailyReport:
    """Generate a structured daily report from today's experiment snapshots.

    Pure computation — no I/O. Caller hydrates snapshots from the event ledger.
    """
    if pending_approvals is None:
        pending_approvals = []

    metrics = _aggregate_metrics(date, snapshots)
    recommendations, risks = _derive_recommendations_and_risks(metrics, snapshots)
    lessons = _derive_lessons(metrics, pending_approvals, recent_mistakes)
    pending_ids = tuple(
        r.approval_id for r in pending_approvals if r.status == ApprovalStatus.PENDING
    )

    return DailyReport(
        date=date,
        metrics=metrics,
        pending_approvals=pending_ids,
        recommendations=recommendations,
        risks=risks,
        lessons=lessons,
    )
