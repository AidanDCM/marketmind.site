"""Slice 19: approved-action executor.

Closes the human-in-the-loop: the runner queues a scale request, a human
approves it, and this module *acts* on the APPROVED record — recording an
audit event in the ledger. It is the hand on the far side of the approval gate.

Safety model (consistent with APPROVAL_POLICY.md):
  - Refuses to act on anything that is not APPROVED. PENDING / DENIED / BLOCKED
    / AUTO_ALLOWED records raise rather than execute.
  - dry_run=True is the default. In dry-run the executor records the *intent*
    in the audit ledger but performs no external effect and spends no money.
  - Live execution (dry_run=False) is refused for actions that have no safe
    integration wired (e.g. ad-budget scaling): safe-fail, never a silent spend.
  - Execution is idempotent per approval_id via the event ledger — an action is
    recorded at most once.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.engine import Engine

from .db import approval_store
from .db.event_store import append_event, event_exists, list_events
from .logging_config import get_logger
from .schemas import ApprovalRecord, ApprovalStatus

log = get_logger(__name__)

_EXECUTION_EVENT = "action_executed"


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
# Action handlers
#
# Each handler returns (detail_dict). It must NOT perform a real money action
# or external call unless dry_run is False AND a safe integration exists.
# Handlers raise ValueError to refuse (safe-fail).
# ---------------------------------------------------------------------------


def _handle_scale_campaign(record: ApprovalRecord, dry_run: bool) -> dict[str, Any]:
    if not dry_run:
        # No ads-platform integration is wired. Refuse rather than pretend.
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


# Registry of action -> handler. Actions without a handler are recorded as
# "no executor registered" (not an error — just nothing to do yet).
_HANDLERS = {
    "scale_campaign": _handle_scale_campaign,
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

    # Idempotency: never execute the same approval twice.
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

    detail = handler(record, dry_run)  # may raise ValueError to refuse

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
