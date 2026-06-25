"""Canonical operator-health strings and formatters (desktop parsers depend on exact text)."""

from __future__ import annotations

import re

OPERATOR_LOG_REL_PATH = "logs/operator_events.jsonl"

OPERATOR_LOG_MISSING_WARNING = (
    f"Operator event log not found at {OPERATOR_LOG_REL_PATH}"
)
GMAIL_LIVE_NOT_READY_WARNING = (
    "MARKETMIND_ENABLE_LIVE_WRITES=true but Gmail is not live-ready"
)
GMAIL_SECRET_MISSING_WARNING = (
    "Gmail live mode enabled but GMAIL_CLIENT_SECRET is missing"
)
STRIPE_LIVE_NOT_READY_WARNING = (
    "MARKETMIND_ENABLE_LIVE_WRITES=true but Stripe is not live-ready "
    "(set STRIPE_API_KEY and MARKETMIND_STRIPE_DRY_RUN=false)"
)
SHOPIFY_LIVE_NOT_READY_WARNING = (
    "MARKETMIND_ENABLE_LIVE_WRITES=true but Shopify is not live-ready "
    "(set store credentials and MARKETMIND_SHOPIFY_READ_ONLY=false)"
)

STRIPE_LIVE_WARNING_PREFIX = STRIPE_LIVE_NOT_READY_WARNING.split(" (")[0]
SHOPIFY_LIVE_WARNING_PREFIX = SHOPIFY_LIVE_NOT_READY_WARNING.split(" (")[0]

ATTENTION_RULINGS = frozenset({"kill", "pause_ads"})

OPERATOR_HEALTH_API_PATHS: tuple[str, ...] = (
    "/operator/preflight",
    "/operator/readiness",
    "/operator/health-panel",
)

OPERATOR_HEALTH_DESKTOP_API_PATHS: tuple[str, ...] = (
    "/operator/integrations",
    "/operator/last-cycle",
    "/operator/checklist-config",
)

OPERATOR_HEALTH_EXTENDED_API_PATHS: tuple[str, ...] = (
    *OPERATOR_HEALTH_DESKTOP_API_PATHS,
    "/operator/snapshot-gaps",
)

OPERATOR_READINESS_STRICT_QUERY = "strict"
OPERATOR_READINESS_DATE_QUERY = "date"
OPERATOR_HEALTH_PANEL_DATE_QUERY = "date"

OPERATOR_READINESS_CLI_API_FLAG = "--api"

OPERATOR_ROUTER_PATH = "marketmind/api/routers/operator.py"
OPERATOR_SNAPSHOT_GAPS_API_PATH = "/operator/snapshot-gaps"
OPERATOR_RUN_CYCLE_API_PATH = "/operator/run-cycle"
OPERATOR_LAST_CYCLE_API_PATH = "/operator/last-cycle"
OPERATOR_SNAPSHOT_GAPS_DATE_QUERY = "date"

OPERATOR_LAST_CYCLE_CYCLE_KEY = "cycle"
OPERATOR_PREFLIGHT_SAFE_TO_OPERATE_KEY = "safe_to_operate"
OPERATOR_PREFLIGHT_PENDING_APPROVALS_KEY = "pending_approvals"
OPERATOR_PREFLIGHT_OPERATOR_LOG_EXISTS_KEY = "operator_log_exists"
OPERATOR_INTEGRATIONS_SUBKEYS: tuple[str, ...] = ("gmail", "stripe", "shopify")
OPERATOR_SNAPSHOT_GAPS_ALL_RECORDED_KEY = "all_recorded"

OPERATOR_CHECKLIST_CONFIG_KEYS: tuple[str, ...] = (
    "min_visits",
    "min_orders",
    "min_spend",
)
OPERATOR_READINESS_EMPTY_DATE_DETAIL = "date must not be empty when provided"
OPERATOR_LAST_CYCLE_HAS_DATA_KEY = "has_data"

DESKTOP_API_CLIENT_PATH = "desktop/src/api/client.ts"
DESKTOP_OPERATOR_HEALTH_PANEL_PATH = "desktop/src/components/OperatorHealthPanel.tsx"
DESKTOP_OPERATOR_HEALTH_PANEL_TEST_PATH = "desktop/src/components/OperatorHealthPanel.test.tsx"
DESKTOP_PREFLIGHT_SUMMARY_ACTIONS_PATH = "desktop/src/preflightSummaryActions.ts"

HEALTH_PANEL_RUN_CYCLE_BUTTON = "Run cycle now"
HEALTH_PANEL_RECORD_SNAPSHOTS_BUTTON = "Record snapshots"
HEALTH_PANEL_VIEW_SNAPSHOTS_BUTTON = "View snapshots"
HEALTH_PANEL_IMPORT_ADS_BUTTON = "Import ads"
HEALTH_PANEL_LAST_CYCLE_TITLE = "Last daily cycle"
HEALTH_PANEL_SNAPSHOTS_FOR_PREFIX = "Snapshots for"

READINESS_BANNER_ACTION_LABELS: dict[str, str] = {
    "approvals": "Open queue",
    "active": "View experiment",
    "snapshots": "Record snapshot",
    "live": "Check Live Data",
}

OPERATOR_READINESS_CLI = "scripts/check_operator_readiness.py"

DESKTOP_READINESS_CONSTANTS_PATH = "desktop/src/readinessBannerActions.ts"

# Mirrors ``desktop/src/readinessBannerActions.ts`` regex parsers.
PENDING_APPROVALS_BLOCKER_PATTERN = re.compile(
    r"^(\d+) pending approval\(s\) have not been reviewed$"
)
EXPERIMENT_RULING_BLOCKER_PATTERN = re.compile(
    r"^Experiment '([^']+)' ruling is '([^']+)' — action required$"
)
MISSING_SNAPSHOT_WARNING_PATTERN = re.compile(
    r"^(\d+) active experiment\(s\) missing snapshot for (\d{4}-\d{2}-\d{2}): (.+)$"
)

SNAPSHOT_GAP_TRUNCATION_LIMIT = 5


def format_pending_approvals_blocker(count: int) -> str:
    return f"{count} pending approval(s) have not been reviewed"


def format_experiment_ruling_blocker(experiment_id: str, ruling: str) -> str:
    return (
        f"Experiment '{experiment_id}' ruling is '{ruling}' — action required"
    )


def format_missing_snapshot_warning(
    missing_count: int,
    snapshot_date: str,
    experiment_ids: list[str],
    *,
    max_ids: int = SNAPSHOT_GAP_TRUNCATION_LIMIT,
) -> str:
    shown = experiment_ids[:max_ids]
    suffix = "…" if missing_count > max_ids else ""
    ids = ", ".join(shown) + suffix
    return (
        f"{missing_count} active experiment(s) missing snapshot "
        f"for {snapshot_date}: {ids}"
    )


__all__ = [
    "ATTENTION_RULINGS",
    "DESKTOP_API_CLIENT_PATH",
    "DESKTOP_OPERATOR_HEALTH_PANEL_PATH",
    "DESKTOP_OPERATOR_HEALTH_PANEL_TEST_PATH",
    "DESKTOP_PREFLIGHT_SUMMARY_ACTIONS_PATH",
    "DESKTOP_READINESS_CONSTANTS_PATH",
    "EXPERIMENT_RULING_BLOCKER_PATTERN",
    "GMAIL_LIVE_NOT_READY_WARNING",
    "GMAIL_SECRET_MISSING_WARNING",
    "HEALTH_PANEL_IMPORT_ADS_BUTTON",
    "HEALTH_PANEL_LAST_CYCLE_TITLE",
    "HEALTH_PANEL_RECORD_SNAPSHOTS_BUTTON",
    "HEALTH_PANEL_RUN_CYCLE_BUTTON",
    "HEALTH_PANEL_SNAPSHOTS_FOR_PREFIX",
    "HEALTH_PANEL_VIEW_SNAPSHOTS_BUTTON",
    "MISSING_SNAPSHOT_WARNING_PATTERN",
    "OPERATOR_CHECKLIST_CONFIG_KEYS",
    "OPERATOR_HEALTH_API_PATHS",
    "OPERATOR_HEALTH_DESKTOP_API_PATHS",
    "OPERATOR_HEALTH_EXTENDED_API_PATHS",
    "OPERATOR_HEALTH_PANEL_DATE_QUERY",
    "OPERATOR_INTEGRATIONS_SUBKEYS",
    "OPERATOR_LAST_CYCLE_API_PATH",
    "OPERATOR_LAST_CYCLE_CYCLE_KEY",
    "OPERATOR_LAST_CYCLE_HAS_DATA_KEY",
    "OPERATOR_LOG_MISSING_WARNING",
    "OPERATOR_LOG_REL_PATH",
    "OPERATOR_PREFLIGHT_OPERATOR_LOG_EXISTS_KEY",
    "OPERATOR_PREFLIGHT_PENDING_APPROVALS_KEY",
    "OPERATOR_PREFLIGHT_SAFE_TO_OPERATE_KEY",
    "OPERATOR_READINESS_CLI",
    "OPERATOR_READINESS_CLI_API_FLAG",
    "OPERATOR_READINESS_DATE_QUERY",
    "OPERATOR_READINESS_EMPTY_DATE_DETAIL",
    "OPERATOR_READINESS_STRICT_QUERY",
    "OPERATOR_ROUTER_PATH",
    "OPERATOR_RUN_CYCLE_API_PATH",
    "OPERATOR_SNAPSHOT_GAPS_ALL_RECORDED_KEY",
    "OPERATOR_SNAPSHOT_GAPS_API_PATH",
    "OPERATOR_SNAPSHOT_GAPS_DATE_QUERY",
    "PENDING_APPROVALS_BLOCKER_PATTERN",
    "READINESS_BANNER_ACTION_LABELS",
    "SHOPIFY_LIVE_NOT_READY_WARNING",
    "SHOPIFY_LIVE_WARNING_PREFIX",
    "SNAPSHOT_GAP_TRUNCATION_LIMIT",
    "STRIPE_LIVE_NOT_READY_WARNING",
    "STRIPE_LIVE_WARNING_PREFIX",
    "format_experiment_ruling_blocker",
    "format_missing_snapshot_warning",
    "format_pending_approvals_blocker",
]
