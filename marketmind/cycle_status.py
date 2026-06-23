"""Daily cycle status from the operator event ledger."""

from __future__ import annotations

from typing import Any

from .event_ledger import get_ledger
from .runner import RunResult

CYCLE_EVENT_TYPE = "runner.daily_cycle"


def record_daily_cycle(result: RunResult) -> None:
    """Append a summary of a completed daily cycle to the operator ledger."""
    ledger = get_ledger()
    payload: dict[str, Any] = {
        "date": result.date,
        "experiments_evaluated": len(result.rulings),
        "approvals_created": len(result.approvals_created),
        "approval_ids": list(result.approvals_created),
        "rulings": [
            {
                "experiment_id": ruling.experiment_id,
                "ruling": ruling.ruling.value,
                "risks": list(ruling.risks),
            }
            for ruling in result.rulings
        ],
        "snapshot_prune": result.snapshot_prune,
    }
    ledger.append(CYCLE_EVENT_TYPE, f"daily-cycle-{result.date}", payload)


def get_last_daily_cycle() -> dict[str, Any] | None:
    """Return the most recent daily cycle ledger entry, if any."""
    for event in reversed(get_ledger().read_tail(300)):
        if event.event_type != CYCLE_EVENT_TYPE:
            continue
        return {
            "event_id": event.event_id,
            "created_at": event.created_at,
            **event.payload,
        }
    return None
