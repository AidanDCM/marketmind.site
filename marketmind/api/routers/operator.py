"""Operator API — preflight check and audit-log endpoints.

Parts-and-Pieces integration (Parts & Pieces → MarketMind):
- GET /operator/preflight  uses marketmind.operator_preflight (from operator_status part)
- POST /operator/log-event uses marketmind.event_ledger       (from event_ledger part)
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ...event_ledger import get_ledger
from ...operator_preflight import run_preflight

router = APIRouter(tags=["operator"])


@router.get("/preflight")
def operator_preflight(request: Request) -> dict:
    """Return operator readiness: pending approvals, experiments needing action, safe_to_operate.

    Run this at the start of every operator session. If ``safe_to_operate`` is
    false, resolve the listed ``blockers`` before executing any high-risk action.
    """
    engine = request.app.state.engine
    status = run_preflight(engine)
    return {
        "safe_to_operate": status.safe_to_operate,
        "pending_approvals": status.pending_approvals,
        "experiments_needing_attention": status.experiments_needing_attention,
        "operator_log_exists": status.operator_log_exists,
        "blockers": status.blockers,
        "summary": status.summary,
    }


class LogEventRequest(BaseModel):
    event_type: str
    event_id: str
    payload: dict = {}


@router.post("/log-event")
def log_operator_event(body: LogEventRequest) -> dict:
    """Append a named event to the operator audit log (logs/operator_events.jsonl).

    Use this to record any significant operator decision:
      - experiment killed / paused / scaled
      - approval granted or denied
      - manual override with reason
      - preflight check passed

    The log is append-only. Entries are never edited or deleted.
    """
    if not body.event_type.strip():
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="event_type must not be empty")
    if not body.event_id.strip():
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="event_id must not be empty")

    ledger = get_ledger()
    event = ledger.append(body.event_type.strip(), body.event_id.strip(), body.payload)
    return {
        "logged": True,
        "event_type": event.event_type,
        "event_id": event.event_id,
        "created_at": event.created_at,
    }
