#!/usr/bin/env python3
"""Print masked Gmail integration readiness (no secrets)."""

from __future__ import annotations

from marketmind.gmail_config import get_gmail_config


def main() -> None:
    cfg = get_gmail_config()
    print(
        {
            "enabled": cfg.enabled,
            "wired": cfg.wired,
            "dry_run": cfg.dry_run,
            "live_ready": cfg.live_ready,
            "mode": cfg.mode,
            "has_client_id": bool(cfg.client_id),
            "has_client_secret": bool(cfg.client_secret),
            "has_refresh_token": bool(cfg.refresh_token),
            "operator_email_set": bool(cfg.operator_email),
        }
    )


if __name__ == "__main__":
    main()
