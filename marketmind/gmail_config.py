"""Gmail integration config (off by default; no API calls here)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class GmailConfig:
    enabled: bool
    wired: bool
    dry_run: bool
    client_id: str
    client_secret: str
    refresh_token: str
    operator_email: str

    @property
    def mode(self) -> str:
        if not self.enabled:
            return "draft_file_only"
        if not self.wired:
            return "enabled_but_unconfigured"
        if self.dry_run:
            return "simulate"
        if not self.client_secret:
            return "live_missing_secret"
        return "live_send"

    @property
    def live_ready(self) -> bool:
        return self.wired and bool(self.client_secret) and not self.dry_run


def get_gmail_config() -> GmailConfig:
    """Read Gmail env flags. Live API requires enabled + OAuth creds + dry_run=false."""
    enabled = _env_flag("MARKETMIND_GMAIL_ENABLED")
    client_id = os.environ.get("GMAIL_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN", "").strip()
    operator_email = os.environ.get("GMAIL_OPERATOR_EMAIL", "").strip()
    wired = enabled and bool(client_id and refresh_token)
    dry_run = _env_flag("MARKETMIND_GMAIL_DRY_RUN", default=True)
    return GmailConfig(
        enabled=enabled,
        wired=wired,
        dry_run=dry_run,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        operator_email=operator_email,
    )


def live_writes_allowed() -> bool:
    return _env_flag("MARKETMIND_ENABLE_LIVE_WRITES")
