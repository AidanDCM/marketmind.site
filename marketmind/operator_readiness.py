"""Operator readiness (local env + DB, or remote API fetch)."""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlencode

from sqlalchemy.engine import Engine

from .commerce_integrations import get_commerce_integration_status
from .gmail_config import get_gmail_config
from .operator_health import build_operator_health


def _default_get(url: str, token: str | None) -> dict:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


@dataclass(frozen=True)
class OperatorReadinessResult:
    ready: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    report: dict

    def to_dict(self) -> dict:
        return {
            "ready": self.ready,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            **self.report,
        }


def masked_gmail_summary() -> dict:
    cfg = get_gmail_config()
    return {
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


def evaluate_operator_readiness(
    engine: Engine,
    *,
    strict: bool = False,
    snapshot_date: str | None = None,
) -> OperatorReadinessResult:
    """Combine Gmail/commerce env checks with local preflight and health warnings."""
    health = build_operator_health(engine, snapshot_date=snapshot_date)
    blockers = tuple(health["preflight"]["blockers"])
    warnings = tuple(health["warnings"])

    ready = health["safe_to_operate"]
    if strict:
        ready = ready and not warnings

    report = {
        "safe_to_operate": health["safe_to_operate"],
        "gmail": masked_gmail_summary(),
        "commerce": get_commerce_integration_status(),
        "live_writes": health["integrations"].get("live_writes", {}),
        "preflight": health["preflight"],
        "snapshot_gaps": health["snapshot_gaps"],
        "last_cycle": health["last_cycle"],
        "portfolio": {
            "total_experiments": health["portfolio"]["total_experiments"],
            "active": health["portfolio"]["active"],
        },
    }

    return OperatorReadinessResult(
        ready=ready,
        blockers=blockers,
        warnings=warnings,
        report=report,
    )


def readiness_from_api_payload(payload: dict) -> OperatorReadinessResult:
    """Parse ``GET /operator/readiness`` JSON into an ``OperatorReadinessResult``."""
    return OperatorReadinessResult(
        ready=bool(payload.get("ready")),
        blockers=tuple(payload.get("blockers", [])),
        warnings=tuple(payload.get("warnings", [])),
        report={
            key: value
            for key, value in payload.items()
            if key not in {"ready", "blockers", "warnings"}
        },
    )


def fetch_operator_readiness_from_api(
    base_url: str,
    token: str | None = None,
    *,
    snapshot_date: str | None = None,
    strict: bool = False,
    fetch: Callable[[str, str | None], dict] | None = None,
) -> OperatorReadinessResult:
    """Fetch readiness from a running MarketMind API."""
    get = fetch or _default_get
    base = base_url.rstrip("/")
    params: dict[str, str] = {}
    if snapshot_date:
        params["date"] = snapshot_date
    if strict:
        params["strict"] = "true"
    query = f"?{urlencode(params)}" if params else ""
    payload = get(f"{base}/operator/readiness{query}", token)
    return readiness_from_api_payload(payload)
