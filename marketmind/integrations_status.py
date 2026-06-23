"""Operator-facing integration readiness (read-only; no external calls)."""

from __future__ import annotations

import os

from sqlalchemy.engine import Engine

from .ad_summary import summarize_latest_ad_batch


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes"}


def get_integrations_status(engine: Engine) -> dict:
    """Return which optional integrations are enabled, wired, or available."""
    gmail_enabled = _env_flag("MARKETMIND_GMAIL_ENABLED")
    gmail_wired = gmail_enabled and bool(
        os.environ.get("GMAIL_CLIENT_ID", "").strip()
        and os.environ.get("GMAIL_REFRESH_TOKEN", "").strip()
    )
    ad_summary = summarize_latest_ad_batch(engine)

    if gmail_wired:
        gmail_mode = "live_send"
    elif gmail_enabled:
        gmail_mode = "enabled_but_unconfigured"
    else:
        gmail_mode = "draft_file_only"

    return {
        "gmail": {
            "enabled": gmail_enabled,
            "wired": gmail_wired,
            "mode": gmail_mode,
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
    }
