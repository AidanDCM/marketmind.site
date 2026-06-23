"""Local operator readiness (env + DB preflight; no external API calls)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.engine import Engine

from .commerce_integrations import get_commerce_integration_status
from .gmail_config import get_gmail_config
from .operator_health import build_operator_health


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


def evaluate_operator_readiness(engine: Engine, *, strict: bool = False) -> OperatorReadinessResult:
    """Combine Gmail/commerce env checks with local preflight and health warnings."""
    health = build_operator_health(engine)
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
