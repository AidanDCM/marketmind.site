#!/usr/bin/env python3
"""Post-deploy verification for MarketMind API."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _get(url: str, token: str | None) -> dict:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    base = os.environ.get("MARKETMIND_API_BASE", "http://127.0.0.1:8000").rstrip("/")
    token = os.environ.get("MARKETMIND_API_TOKEN") or None
    failures: list[str] = []

    try:
        health = _get(f"{base}/health", token)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"FAIL health: {exc}")
        return 1

    if health.get("status") != "ok":
        failures.append(f"health.status != ok ({health!r})")
    else:
        print(f"OK  GET /health -> {health.get('version', '?')}")

    try:
        panel = _get(f"{base}/operator/health-panel", token)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"FAIL operator/health-panel: {exc}")
        return 1

    print(f"OK  GET /operator/health-panel -> safe_to_operate={panel.get('safe_to_operate')}")
    for warning in panel.get("warnings", []):
        print(f"WARN {warning}")
    for blocker in panel.get("preflight", {}).get("blockers", []):
        failures.append(f"preflight blocker: {blocker}")

    if failures:
        for item in failures:
            print(f"FAIL {item}")
        return 1

    print("Deploy verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
