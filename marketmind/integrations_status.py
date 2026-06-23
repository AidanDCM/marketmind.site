"""Operator-facing integration readiness (read-only; no external calls)."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from .ad_summary import summarize_latest_ad_batch
from .gmail_config import _env_flag, get_gmail_config


def get_integrations_status(engine: Engine) -> dict:
    """Return which optional integrations are enabled, wired, or available."""
    gmail = get_gmail_config()
    ad_summary = summarize_latest_ad_batch(engine)

    return {
        "gmail": {
            "enabled": gmail.enabled,
            "wired": gmail.wired,
            "dry_run": gmail.dry_run,
            "live_ready": gmail.live_ready,
            "mode": gmail.mode,
        },
        "ad_imports": {
            "csv_available": True,
            "has_latest_batch": ad_summary is not None,
            "latest_batch_id": ad_summary.batch_id if ad_summary else None,
        },
        "scheduler": {
            "prune_on_cycle": _env_flag("MARKETMIND_SNAPSHOT_PRUNE_ON_CYCLE"),
            "prune_apply": _env_flag("MARKETMIND_SNAPSHOT_PRUNE_APPLY"),
        },
        "live_writes": {
            "enabled": _env_flag("MARKETMIND_ENABLE_LIVE_WRITES"),
        },
    }
