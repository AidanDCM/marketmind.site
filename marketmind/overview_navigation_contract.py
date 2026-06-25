"""Canonical Overview navigation facts (API paths, preferences, report phrases)."""

from __future__ import annotations

from .experiment_lifecycle_contract import (
    NO_EXPERIMENTS_RECOMMENDATION,
    SCALE_APPROVAL_PHRASE,
)

# GET paths the Overview page fetches on load (see ``desktop/src/api/client.ts``).
OVERVIEW_FETCH_API_PATHS: tuple[str, ...] = (
    "/report/daily",
    "/approvals/pending",
    "/operator/health-panel",
    "/operator/readiness",
    "/experiment/trend-summary",
)

OVERVIEW_RUN_CYCLE_PATH = "/operator/run-cycle"
OVERVIEW_PENDING_APPROVALS_PATH = "/approvals/pending"
OVERVIEW_RUN_CYCLE_DATE_QUERY = "date"
OVERVIEW_RUN_CYCLE_EMPTY_DATE_DETAIL = "date must not be empty when provided"

OVERVIEW_LOCAL_STORAGE_KEYS: tuple[str, ...] = (
    "marketmind_attention_only",
    "marketmind_trend_days",
    "marketmind_overview_date",
)

LOOKBACK_DAY_OPTIONS: tuple[int, ...] = (7, 14, 30, 60, 90)
DEFAULT_LOOKBACK_DAYS = 14

DESKTOP_OVERVIEW_PREFERENCES_PATH = "desktop/src/components/overviewPreferences.ts"
DESKTOP_LOOKBACK_OPTIONS_PATH = "desktop/src/lookbackOptions.ts"
DESKTOP_OVERVIEW_COMPONENT_PATH = "desktop/src/components/Overview.tsx"
DESKTOP_API_CLIENT_PATH = "desktop/src/api/client.ts"
DESKTOP_OVERVIEW_TEST_PATH = "desktop/src/components/Overview.test.tsx"

DESKTOP_OVERVIEW_DAILY_CYCLE_PATH = "desktop/src/overviewDailyCycle.ts"
DESKTOP_OVERVIEW_TREND_EMPTY_STATE_PATH = "desktop/src/components/OverviewTrendEmptyState.tsx"

OVERVIEW_TREND_SUMMARY_API_PATH = "/experiment/trend-summary"
DAILY_REPORT_API_PATH = "/report/daily"

EXPERIMENTS_ROUTER_PATH = "marketmind/api/routers/experiments.py"
REPORTS_ROUTER_PATH = "marketmind/api/routers/reports.py"

DAILY_REPORT_DATE_QUERY = "date"

TREND_AS_OF_EMPTY_DETAIL = "as_of must not be empty when provided"
TREND_AS_OF_ISO_DETAIL = "as_of must be an ISO date"
TREND_DAYS_MIN_FRAGMENT = "days must be at least 1"
TREND_DAYS_MAX_FRAGMENT = "days must be at most 90"
TREND_ATTENTION_ONLY_QUERY = "attention_only"

TREND_SUMMARY_RESPONSE_KEYS: tuple[str, ...] = (
    "days",
    "as_of",
    "needs_attention_count",
    "experiments",
)

DAILY_REPORT_RESPONSE_DATE_KEY = "date"
DAILY_REPORT_RESPONSE_KEYS: tuple[str, ...] = (
    "date",
    "metrics",
    "pending_approvals",
    "recommendations",
    "risks",
    "lessons",
)

OVERVIEW_PAGE_TITLE = "Overview"
OVERVIEW_ATTENTION_EMPTY_BUTTON = "View all experiments"
OVERVIEW_TREND_EMPTY_STATE_ATTENTION_PREFIX = "No active experiments need attention for"

OVERVIEW_TREND_QUERY_PARAMS: tuple[str, ...] = (
    "days",
    "as_of",
    TREND_ATTENTION_ONLY_QUERY,
)

TREND_LOOKBACK_LABEL = "Lookback"
TREND_ATTENTION_ONLY_LABEL = "Attention only"

OVERVIEW_SNAPSHOTS_HEADER_BUTTON = "Snapshots"
SNAPSHOT_STALE_RECORD_BUTTON = "Record"

__all__ = [
    "DAILY_REPORT_API_PATH",
    "DAILY_REPORT_DATE_QUERY",
    "DAILY_REPORT_RESPONSE_DATE_KEY",
    "DAILY_REPORT_RESPONSE_KEYS",
    "DEFAULT_LOOKBACK_DAYS",
    "DESKTOP_API_CLIENT_PATH",
    "DESKTOP_LOOKBACK_OPTIONS_PATH",
    "DESKTOP_OVERVIEW_COMPONENT_PATH",
    "DESKTOP_OVERVIEW_DAILY_CYCLE_PATH",
    "DESKTOP_OVERVIEW_PREFERENCES_PATH",
    "DESKTOP_OVERVIEW_TEST_PATH",
    "DESKTOP_OVERVIEW_TREND_EMPTY_STATE_PATH",
    "EXPERIMENTS_ROUTER_PATH",
    "LOOKBACK_DAY_OPTIONS",
    "NO_EXPERIMENTS_RECOMMENDATION",
    "OVERVIEW_ATTENTION_EMPTY_BUTTON",
    "OVERVIEW_FETCH_API_PATHS",
    "OVERVIEW_LOCAL_STORAGE_KEYS",
    "OVERVIEW_PAGE_TITLE",
    "OVERVIEW_PENDING_APPROVALS_PATH",
    "OVERVIEW_RUN_CYCLE_DATE_QUERY",
    "OVERVIEW_RUN_CYCLE_EMPTY_DATE_DETAIL",
    "OVERVIEW_RUN_CYCLE_PATH",
    "OVERVIEW_SNAPSHOTS_HEADER_BUTTON",
    "OVERVIEW_TREND_EMPTY_STATE_ATTENTION_PREFIX",
    "OVERVIEW_TREND_QUERY_PARAMS",
    "OVERVIEW_TREND_SUMMARY_API_PATH",
    "REPORTS_ROUTER_PATH",
    "SCALE_APPROVAL_PHRASE",
    "SNAPSHOT_STALE_RECORD_BUTTON",
    "TREND_AS_OF_EMPTY_DETAIL",
    "TREND_AS_OF_ISO_DETAIL",
    "TREND_ATTENTION_ONLY_LABEL",
    "TREND_ATTENTION_ONLY_QUERY",
    "TREND_DAYS_MAX_FRAGMENT",
    "TREND_DAYS_MIN_FRAGMENT",
    "TREND_LOOKBACK_LABEL",
    "TREND_SUMMARY_RESPONSE_KEYS",
]
