"""Canonical experiment-lifecycle strings (desktop parsers depend on exact text)."""

from __future__ import annotations

NO_EXPERIMENTS_RECOMMENDATION = (
    "No experiments active today. Pick a product candidate to test."
)
ZERO_ORDER_SPEND_RISK = (
    "Spend with zero orders today — check targeting and offer."
)
SCALE_APPROVAL_PHRASE = "submit scale request for approval"
POSITIVE_CONTRIBUTION_PREFIX = "Positive contribution today"
NO_ORDERS_LESSON_PREFIX = (
    "No orders: verify that the payment link / checkout is live and working."
)
ROAS_SCALE_LESSON_PHRASE = "confirm with experiment rules before scaling."
LOW_ROAS_LESSON_MARKER = "(below 1.0)"
PAST_LESSON_PREFIX = "Past lesson: "
REFUND_RISK_SUFFIX = " — review product quality."
ATC_RISK_SUFFIX = " — creative or price needs revision."

ATTENTION_RULINGS = frozenset({"kill", "pause_ads", "scale_requires_approval"})

DESKTOP_DAILY_REPORT_NAVIGATION_PATH = "desktop/src/dailyReportNavigation.ts"
DESKTOP_EXPERIMENT_ATTENTION_PATH = "desktop/src/experimentAttention.ts"
