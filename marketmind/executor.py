"""Slice 19-20: approved-action executor.

Closes the human-in-the-loop: a request is queued, a human approves it, and this
module *acts* on the APPROVED record — recording an audit event in the ledger.
It is the hand on the far side of the approval gate.

Action payloads (what to actually send for Stripe/Shopify actions) are carried
in the append-only event ledger as an ``approval_payload`` event keyed by the
approval id — no schema change to the approvals table. Attach one with
``record_action_payload`` when you create the approval.

Safety model (consistent with APPROVAL_POLICY.md):
  - Refuses to act on anything that is not APPROVED.
  - dry_run=True is the default. In dry-run, adapter actions go through the
    gate-enforced ``simulate_*`` helpers (no HTTP, no money); other actions
    record their intent only.
  - Live execution (dry_run=False) requires credentials in the environment and
    is refused (safe-fail) when they are missing or no integration is wired.
  - Execution is idempotent per approval_id via the event ledger.
  - Secrets (API keys/tokens) are never logged or returned.
"""

from __future__ import annotations

import dataclasses
import os
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.engine import Engine

from .adapters.shopify_client import ShopifyClient, simulate_create_product_draft
from .adapters.stripe_client import StripeClient, simulate_create_payment_link
from .db import approval_store
from .db.event_store import append_event, event_exists, list_events
from .logging_config import get_logger
from .schemas import (
    ApprovalRecord,
    ApprovalStatus,
    PaymentLinkPayload,
    ProductDraftPayload,
    ShopifyVariant,
)

log = get_logger(__name__)

_EXECUTION_EVENT = "action_executed"
_PAYLOAD_EVENT = "approval_payload"


@dataclass
class ExecutionResult:
    """Outcome of attempting to execute one approved action."""

    approval_id: str
    action: str
    executed: bool
    dry_run: bool
    reason: str = ""
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "action": self.action,
            "executed": self.executed,
            "dry_run": self.dry_run,
            "reason": self.reason,
            "detail": dict(self.detail),
        }


# ---------------------------------------------------------------------------
# Payload carriage (via the event ledger — no approvals-table schema change)
# ---------------------------------------------------------------------------


def record_action_payload(engine: Engine, approval_id: str, payload: dict[str, Any]) -> None:
    """Attach the action payload for an approval (stored in the event ledger)."""
    append_event(engine, _PAYLOAD_EVENT, approval_id, payload=payload)


def _load_payload(engine: Engine, approval_id: str) -> dict[str, Any] | None:
    events = [
        e
        for e in list_events(engine, event_type=_PAYLOAD_EVENT)
        if e["event_id"] == approval_id
    ]
    return events[-1]["payload"] if events else None


# ---------------------------------------------------------------------------
# Action handlers — each takes (engine, record, dry_run) and returns a detail
# dict, or raises ValueError to refuse (safe-fail). Never log/return secrets.
# ---------------------------------------------------------------------------


def _handle_scale_campaign(engine: Engine, record: ApprovalRecord, dry_run: bool) -> dict[str, Any]:
    if not dry_run:
        raise ValueError(
            "Live scale execution is not available: no ad-platform integration "
            "is wired. Apply the budget change manually, or run in dry_run mode "
            "to record the approved intent."
        )
    return {
        "kind": "scale_campaign",
        "approved_budget": record.expected_cost,
        "note": "Dry-run: approved scale recorded in the ledger; no live spend.",
    }


def _handle_create_stripe_payment_link(
    engine: Engine, record: ApprovalRecord, dry_run: bool
) -> dict[str, Any]:
    raw = _load_payload(engine, record.approval_id)
    if raw is None:
        raise ValueError(
            f"No payload recorded for {record.approval_id!r}. "
            "Attach one with record_action_payload() before executing."
        )
    payload = PaymentLinkPayload(**raw)

    if dry_run:
        result = simulate_create_payment_link(dataclasses.replace(payload, dry_run=True), record)
        return {"kind": "stripe_payment_link", "simulated": True, "id": result.get("id")}

    api_key = os.environ.get("STRIPE_API_KEY", "")
    if not api_key.strip():
        raise ValueError(
            "Live Stripe execution requires STRIPE_API_KEY in the environment."
        )
    client = StripeClient(api_key)
    result = client.create_payment_link(dataclasses.replace(payload, dry_run=False), record)
    return {"kind": "stripe_payment_link", "simulated": False, "id": result.get("id")}


def _handle_publish_shopify_product(
    engine: Engine, record: ApprovalRecord, dry_run: bool
) -> dict[str, Any]:
    raw = _load_payload(engine, record.approval_id)
    if raw is None:
        raise ValueError(
            f"No payload recorded for {record.approval_id!r}. "
            "Attach one with record_action_payload() before executing."
        )
    variants = tuple(ShopifyVariant(**v) for v in raw.get("variants", []))
    payload = ProductDraftPayload(**{**raw, "variants": variants})

    if dry_run:
        result = simulate_create_product_draft(dataclasses.replace(payload, dry_run=True), record)
        return {
            "kind": "shopify_product",
            "simulated": True,
            "id": result.get("product", {}).get("id"),
        }

    domain = os.environ.get("SHOPIFY_STORE_DOMAIN", "")
    token = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
    if not domain.strip() or not token.strip():
        raise ValueError(
            "Live Shopify execution requires SHOPIFY_STORE_DOMAIN and "
            "SHOPIFY_ACCESS_TOKEN in the environment."
        )
    client = ShopifyClient(domain, token)
    result = client.create_product_draft(dataclasses.replace(payload, dry_run=False), record)
    return {
        "kind": "shopify_product",
        "simulated": False,
        "id": result.get("product", {}).get("id"),
    }


_HANDLERS = {
    "scale_campaign": _handle_scale_campaign,
    "create_stripe_payment_link": _handle_create_stripe_payment_link,
    "publish_shopify_product": _handle_publish_shopify_product,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def execute_approved(
    engine: Engine,
    approval_id: str,
    dry_run: bool = True,
) -> ExecutionResult:
    """Execute a single APPROVED action, idempotently.

    Raises KeyError if the approval does not exist.
    Raises ValueError if the record is not APPROVED, or a handler refuses.
    """
    record = approval_store.get_approval(engine, approval_id)
    if record is None:
        raise KeyError(f"Approval {approval_id!r} not found.")

    if record.status != ApprovalStatus.APPROVED:
        raise ValueError(
            f"Refusing to execute {approval_id!r}: status is "
            f"{record.status.value!r}, not 'approved'."
        )

    if event_exists(engine, _EXECUTION_EVENT, approval_id):
        return ExecutionResult(
            approval_id=approval_id,
            action=record.action,
            executed=False,
            dry_run=dry_run,
            reason="already_executed",
        )

    handler = _HANDLERS.get(record.action)
    if handler is None:
        return ExecutionResult(
            approval_id=approval_id,
            action=record.action,
            executed=False,
            dry_run=dry_run,
            reason="no executor registered for this action",
        )

    detail = handler(engine, record, dry_run)  # may raise ValueError to refuse

    append_event(
        engine,
        _EXECUTION_EVENT,
        approval_id,
        payload={"action": record.action, "dry_run": dry_run, "detail": detail},
    )
    log.info(
        "approved action executed",
        extra={"approval_id": approval_id, "action": record.action, "dry_run": dry_run},
    )
    return ExecutionResult(
        approval_id=approval_id,
        action=record.action,
        executed=True,
        dry_run=dry_run,
        detail=detail,
    )


def execute_all_approved(engine: Engine, dry_run: bool = True) -> list[ExecutionResult]:
    """Execute every APPROVED action that has not yet been executed.

    Refusals from individual handlers are captured as non-executed results so a
    single un-runnable action never blocks the rest of the batch.
    """
    results: list[ExecutionResult] = []
    for record in approval_store.list_approvals(engine, status=ApprovalStatus.APPROVED):
        try:
            results.append(execute_approved(engine, record.approval_id, dry_run=dry_run))
        except ValueError as exc:
            results.append(
                ExecutionResult(
                    approval_id=record.approval_id,
                    action=record.action,
                    executed=False,
                    dry_run=dry_run,
                    reason=str(exc),
                )
            )
    return results


def execution_log(engine: Engine) -> list[dict[str, Any]]:
    """Return the append-only log of executed actions, oldest first."""
    return list_events(engine, event_type=_EXECUTION_EVENT)
