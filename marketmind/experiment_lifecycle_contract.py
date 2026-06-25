"""Canonical experiment-lifecycle strings (desktop parsers depend on exact text)."""

from __future__ import annotations

import re

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

LIFECYCLE_API_PATHS: tuple[str, ...] = (
    "/experiment/active",
    "/experiment/trend-summary",
    "/experiment/portfolio",
    "/report/daily",
)

EVALUATE_API_PATH = "/experiment/evaluate"

DESKTOP_DAILY_REPORT_NAVIGATION_PATH = "desktop/src/dailyReportNavigation.ts"
DESKTOP_EXPERIMENT_ATTENTION_PATH = "desktop/src/experimentAttention.ts"
DESKTOP_ACTIVE_EXPERIMENTS_TEST_PATH = "desktop/src/components/ActiveExperiments.test.tsx"

PENDING_APPROVALS_LESSON_PATTERN = re.compile(
    r"^(\d+) approval\(s\) pending — unblocking these may unlock next steps\.$"
)


def format_pending_approvals_lesson(count: int) -> str:
    return f"{count} approval(s) pending — unblocking these may unlock next steps."


__all__ = [
    "ATC_RISK_SUFFIX",
    "ATTENTION_RULINGS",
    "DESKTOP_ACTIVE_EXPERIMENTS_TEST_PATH",
    "DESKTOP_DAILY_REPORT_NAVIGATION_PATH",
    "DESKTOP_EXPERIMENT_ATTENTION_PATH",
    "EVALUATE_API_PATH",
    "LIFECYCLE_API_PATHS",
    "LOW_ROAS_LESSON_MARKER",
    "NO_EXPERIMENTS_RECOMMENDATION",
    "NO_ORDERS_LESSON_PREFIX",
    "PAST_LESSON_PREFIX",
    "PENDING_APPROVALS_LESSON_PATTERN",
    "POSITIVE_CONTRIBUTION_PREFIX",
    "REFUND_RISK_SUFFIX",
    "ROAS_SCALE_LESSON_PHRASE",
    "SCALE_APPROVAL_PHRASE",
    "ZERO_ORDER_SPEND_RISK",
    "format_pending_approvals_lesson",
]
