"""Post-deploy API verification (health + operator health-panel)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field

from .deploy_ci_contract import INTEGRATIONS_SECRET_LEAK_MARKERS


def _default_get(url: str, token: str | None) -> dict:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


@dataclass(frozen=True)
class DeployVerifyResult:
    ok: bool
    failures: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    health_version: str | None = None
    safe_to_operate: bool | None = None
    ready: bool | None = None
    lines: tuple[str, ...] = field(default_factory=tuple)


def _integrations_response_is_secret_free(payload: dict) -> str | None:
    text = json.dumps(payload)
    for marker in INTEGRATIONS_SECRET_LEAK_MARKERS:
        if marker in text:
            return f"integrations response contains forbidden substring {marker!r}"
    return None


def verify_marketmind_deploy(
    base_url: str,
    token: str | None = None,
    *,
    fetch: Callable[[str, str | None], dict] | None = None,
) -> DeployVerifyResult:
    """Check /health and /operator/health-panel on a running MarketMind API."""
    get = fetch or _default_get
    base = base_url.rstrip("/")
    failures: list[str] = []
    warnings: list[str] = []
    lines: list[str] = []

    try:
        health = get(f"{base}/health", token)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return DeployVerifyResult(
            ok=False,
            failures=(f"health: {exc}",),
            lines=(f"FAIL health: {exc}",),
        )

    health_version = health.get("version")
    if health.get("status") != "ok":
        failures.append(f"health.status != ok ({health!r})")
        lines.extend(f"FAIL {item}" for item in failures)
        return DeployVerifyResult(
            ok=False,
            failures=tuple(failures),
            health_version=health_version,
            lines=tuple(lines),
        )

    lines.append(f"OK  GET /health -> {health_version or '?'}")

    try:
        panel = get(f"{base}/operator/health-panel", token)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return DeployVerifyResult(
            ok=False,
            failures=(f"operator/health-panel: {exc}",),
            lines=tuple(lines) + (f"FAIL operator/health-panel: {exc}",),
            health_version=health_version,
        )

    safe = panel.get("safe_to_operate")
    lines.append(f"OK  GET /operator/health-panel -> safe_to_operate={safe}")
    for warning in panel.get("warnings", []):
        warnings.append(str(warning))
        lines.append(f"WARN {warning}")
    for blocker in panel.get("preflight", {}).get("blockers", []):
        failures.append(f"preflight blocker: {blocker}")

    try:
        readiness = get(f"{base}/operator/readiness", token)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return DeployVerifyResult(
            ok=False,
            failures=(f"operator/readiness: {exc}",),
            lines=tuple(lines) + (f"FAIL operator/readiness: {exc}",),
            health_version=health_version,
            safe_to_operate=safe if isinstance(safe, bool) else None,
        )

    operator_ready = readiness.get("ready")
    lines.append(f"OK  GET /operator/readiness -> ready={operator_ready}")
    if operator_ready is not True:
        failures.append("operator readiness not ready")
        for blocker in readiness.get("blockers", []):
            failures.append(f"readiness blocker: {blocker}")

    try:
        integrations = get(f"{base}/operator/integrations", token)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return DeployVerifyResult(
            ok=False,
            failures=(f"operator/integrations: {exc}",),
            lines=tuple(lines) + (f"FAIL operator/integrations: {exc}",),
            health_version=health_version,
            safe_to_operate=safe if isinstance(safe, bool) else None,
            ready=operator_ready if isinstance(operator_ready, bool) else None,
        )

    stripe_cfg = integrations.get("stripe", {}).get("configured")
    shopify_cfg = integrations.get("shopify", {}).get("configured")
    lines.append(
        f"OK  GET /operator/integrations -> "
        f"stripe.configured={stripe_cfg} shopify.configured={shopify_cfg}"
    )
    leak_reason = _integrations_response_is_secret_free(integrations)
    if leak_reason:
        failures.append(leak_reason)

    ok = not failures
    if ok:
        lines.append("Deploy verification passed.")
    else:
        lines.extend(f"FAIL {item}" for item in failures)

    return DeployVerifyResult(
        ok=ok,
        failures=tuple(failures),
        warnings=tuple(warnings),
        health_version=health_version,
        safe_to_operate=safe if isinstance(safe, bool) else None,
        ready=operator_ready if isinstance(operator_ready, bool) else None,
        lines=tuple(lines),
    )
