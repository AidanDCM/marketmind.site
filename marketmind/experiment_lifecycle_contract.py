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

VALID_EXPERIMENT_STATUSES: frozenset[str] = frozenset({"active", "ended"})
EXPERIMENT_STATUS_ACTIVE = "active"
EXPERIMENT_STATUS_ENDED = "ended"

STATUS_PATCH_BODY_KEY = "status"
NOTE_BODY_KEY = "body"

STATUS_PATCH_RESPONSE_KEYS: tuple[str, ...] = (
    "experiment_id",
    "status",
    "ended_at",
)

EVALUATE_RESPONSE_KEYS: tuple[str, ...] = (
    "experiment_id",
    "product_name",
    "ruling",
    "risks",
    "reason_summary",
    "requires_approval",
)

NOTE_RESPONSE_KEYS: tuple[str, ...] = (
    "id",
    "experiment_id",
    "created_at",
    "body",
)

CHECKLIST_RESPONSE_KEYS: tuple[str, ...] = (
    "experiment_id",
    "product_name",
    "ready",
    "blockers",
    "items",
)

CHECKLIST_ITEM_KEYS: tuple[str, ...] = (
    "item_id",
    "description",
    "required",
    "passed",
    "evidence",
)

MISTAKES_RESPONSE_KEYS: tuple[str, ...] = (
    "experiment_id",
    "product_name",
    "recorded",
    "suggested",
)

LIFECYCLE_API_PATHS: tuple[str, ...] = (
    "/experiment/active",
    "/experiment/trend-summary",
    "/experiment/portfolio",
    "/report/daily",
)

LIFECYCLE_EXPERIMENT_DETAIL_SUFFIXES: tuple[str, ...] = (
    "status",
    "notes",
    "checklist",
    "mistakes",
)

ACTIVE_STATUS_FILTERS: tuple[str, ...] = ("all", "active", "ended")

ACTIVE_LOCAL_STORAGE_KEYS: tuple[str, ...] = (
    "marketmind_active_attention_only",
    "marketmind_active_status_filter",
)

EVALUATE_API_PATH = "/experiment/evaluate"

EXPERIMENTS_ROUTER_PATH = "marketmind/api/routers/experiments.py"

STATUS_PATCH_INVALID_FRAGMENT = "status must be one of"
NOTE_EMPTY_BODY_DETAIL = "Note body must not be empty"
EXPERIMENT_NOT_FOUND_DETAIL = "Experiment not found"

PORTFOLIO_RESPONSE_KEYS: tuple[str, ...] = (
    "total_experiments",
    "active",
    "ended",
    "needs_attention",
    "by_ruling",
    "lessons_recorded",
)

ACTIVE_EXPERIMENT_ENTRY_KEYS: tuple[str, ...] = (
    "experiment_id",
    "product_name",
    "break_even_cac",
    "status",
    "started_at",
    "ended_at",
    "latest_snapshot_date",
    "ruling",
    "risks",
    "actual_cac",
)

ACTIVE_NOTES_PLACEHOLDER = "Add a note…"
ACTIVE_NOTES_ADD_BUTTON = "Add"
ACTIVE_NOTES_EMPTY_LABEL = "No notes yet."

DESKTOP_DAILY_REPORT_NAVIGATION_PATH = "desktop/src/dailyReportNavigation.ts"
DESKTOP_EXPERIMENT_ATTENTION_PATH = "desktop/src/experimentAttention.ts"
DESKTOP_ACTIVE_EXPERIMENTS_TEST_PATH = "desktop/src/components/ActiveExperiments.test.tsx"
DESKTOP_ACTIVE_EXPERIMENTS_COMPONENT_PATH = (
    "desktop/src/components/ActiveExperiments.tsx"
)
DESKTOP_ACTIVE_EXPERIMENTS_PREFERENCES_PATH = (
    "desktop/src/components/activeExperimentsPreferences.ts"
)
DESKTOP_API_CLIENT_PATH = "desktop/src/api/client.ts"

ACTIVE_ATTENTION_FILTER_LABEL = "Needs attention"
ACTIVE_CHECKLIST_HEADER = "Scale-readiness checklist"
ACTIVE_CHECKLIST_READY_LABEL = "Ready to scale"
ACTIVE_CHECKLIST_NOT_READY_LABEL = "Not ready"
ACTIVE_LESSONS_HEADER = "Lessons learned"
ACTIVE_NOTES_HEADER = "Notes"
ACTIVE_END_BUTTON = "End experiment"
ACTIVE_REACTIVATE_BUTTON = "Reactivate"
ACTIVE_CHART_BUTTON = "Chart"
ACTIVE_ATTENTION_BANNER_FRAGMENT = "require attention"


def experiment_detail_path(experiment_id: str, suffix: str) -> str:
    return f"/experiment/{experiment_id}/{suffix}"

PENDING_APPROVALS_LESSON_PATTERN = re.compile(
    r"^(\d+) approval\(s\) pending — unblocking these may unlock next steps\.$"
)


def format_pending_approvals_lesson(count: int) -> str:
    return f"{count} approval(s) pending — unblocking these may unlock next steps."


__all__ = [
    "ACTIVE_ATTENTION_BANNER_FRAGMENT",
    "ACTIVE_ATTENTION_FILTER_LABEL",
    "ACTIVE_CHART_BUTTON",
    "ACTIVE_CHECKLIST_HEADER",
    "ACTIVE_CHECKLIST_NOT_READY_LABEL",
    "ACTIVE_CHECKLIST_READY_LABEL",
    "ACTIVE_END_BUTTON",
    "ACTIVE_EXPERIMENT_ENTRY_KEYS",
    "ACTIVE_LESSONS_HEADER",
    "ACTIVE_LOCAL_STORAGE_KEYS",
    "ACTIVE_NOTES_ADD_BUTTON",
    "ACTIVE_NOTES_EMPTY_LABEL",
    "ACTIVE_NOTES_HEADER",
    "ACTIVE_NOTES_PLACEHOLDER",
    "ACTIVE_REACTIVATE_BUTTON",
    "ACTIVE_STATUS_FILTERS",
    "ATC_RISK_SUFFIX",
    "ATTENTION_RULINGS",
    "CHECKLIST_ITEM_KEYS",
    "CHECKLIST_RESPONSE_KEYS",
    "DESKTOP_ACTIVE_EXPERIMENTS_COMPONENT_PATH",
    "DESKTOP_ACTIVE_EXPERIMENTS_PREFERENCES_PATH",
    "DESKTOP_ACTIVE_EXPERIMENTS_TEST_PATH",
    "DESKTOP_API_CLIENT_PATH",
    "DESKTOP_DAILY_REPORT_NAVIGATION_PATH",
    "DESKTOP_EXPERIMENT_ATTENTION_PATH",
    "EVALUATE_API_PATH",
    "EVALUATE_RESPONSE_KEYS",
    "EXPERIMENT_NOT_FOUND_DETAIL",
    "EXPERIMENT_STATUS_ACTIVE",
    "EXPERIMENT_STATUS_ENDED",
    "EXPERIMENTS_ROUTER_PATH",
    "LIFECYCLE_API_PATHS",
    "LIFECYCLE_EXPERIMENT_DETAIL_SUFFIXES",
    "LOW_ROAS_LESSON_MARKER",
    "MISTAKES_RESPONSE_KEYS",
    "NO_EXPERIMENTS_RECOMMENDATION",
    "NO_ORDERS_LESSON_PREFIX",
    "NOTE_BODY_KEY",
    "NOTE_EMPTY_BODY_DETAIL",
    "NOTE_RESPONSE_KEYS",
    "PAST_LESSON_PREFIX",
    "PENDING_APPROVALS_LESSON_PATTERN",
    "PORTFOLIO_RESPONSE_KEYS",
    "POSITIVE_CONTRIBUTION_PREFIX",
    "REFUND_RISK_SUFFIX",
    "ROAS_SCALE_LESSON_PHRASE",
    "SCALE_APPROVAL_PHRASE",
    "STATUS_PATCH_BODY_KEY",
    "STATUS_PATCH_INVALID_FRAGMENT",
    "STATUS_PATCH_RESPONSE_KEYS",
    "VALID_EXPERIMENT_STATUSES",
    "ZERO_ORDER_SPEND_RISK",
    "experiment_detail_path",
    "format_pending_approvals_lesson",
]
