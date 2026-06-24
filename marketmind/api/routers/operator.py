"""Operator API — preflight check, audit-log, and mistake-tracker endpoints.

Parts-and-Pieces integration (Parts & Pieces → MarketMind):
- GET /operator/preflight  uses marketmind.operator_preflight (from operator_status part)
- POST /operator/log-event uses marketmind.event_ledger       (from event_ledger part)
- GET/POST /operator/mistakes uses marketmind.mistake_tracker (from mistake_tracker part)
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ...checklist_config import get_checklist_thresholds
from ...cycle_status import get_last_daily_cycle
from ...event_ledger import get_ledger
from ...integrations_status import get_integrations_status
from ...mistake_tracker import VALID_CATEGORIES, get_mistake_tracker
from ...operator_health import build_operator_health
from ...operator_preflight import run_preflight
from ...operator_readiness import evaluate_operator_readiness
from ...snapshot_gaps import list_snapshot_gaps

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


@router.get("/checklist-config")
def operator_checklist_config() -> dict:
    """Return the active scale-readiness thresholds (from env vars)."""
    t = get_checklist_thresholds()
    return {
        "min_visits": t.min_visits,
        "min_orders": t.min_orders,
        "min_spend": t.min_spend,
    }


@router.get("/integrations")
def operator_integrations(request: Request) -> dict:
    """Return optional integration readiness (Gmail, ad CSV, scheduler prune flags)."""
    engine = request.app.state.engine
    return get_integrations_status(engine)


@router.get("/health-panel")
def operator_health_panel(request: Request, date: str | None = None) -> dict:
    """Consolidated operator health: preflight, integrations, portfolio, ad spend, checklist.

    Optional ``date`` (ISO) scopes snapshot-gap detection to that day (default today).
    """
    if date is not None and not date.strip():
        raise HTTPException(status_code=422, detail="date must not be empty when provided")
    engine = request.app.state.engine
    return build_operator_health(engine, snapshot_date=date)


@router.get("/readiness")
def operator_readiness(
    request: Request,
    date: str | None = None,
    strict: bool = False,
) -> dict:
    """Unified operator readiness: Gmail/commerce env, preflight, and health warnings.

    Optional ``date`` scopes snapshot-gap detection. ``strict=true`` fails when warnings exist.
    """
    if date is not None and not date.strip():
        raise HTTPException(status_code=422, detail="date must not be empty when provided")
    engine = request.app.state.engine
    return evaluate_operator_readiness(
        engine,
        strict=strict,
        snapshot_date=date,
    ).to_dict()


@router.get("/last-cycle")
def operator_last_cycle() -> dict:
    """Return the most recent daily cycle recorded in the operator ledger."""
    last = get_last_daily_cycle()
    if last is None:
        return {"has_data": False, "cycle": None}
    return {"has_data": True, "cycle": last}


@router.post("/run-cycle")
def operator_run_cycle(request: Request, date: str | None = None) -> dict:
    """Run one daily experiment cycle (safe — no external API calls or spend).

    Evaluates snapshots, queues scale approvals, generates the daily report,
    and records the outcome in the operator ledger. Optional ``date`` (ISO) defaults
    to today.
    """
    from ...runner import run_daily_cycle

    if date is not None and not date.strip():
        raise HTTPException(status_code=422, detail="date must not be empty when provided")
    engine = request.app.state.engine
    result = run_daily_cycle(engine, date=date)
    return result.to_dict()


@router.get("/snapshot-gaps")
def operator_snapshot_gaps(request: Request, date: str | None = None) -> dict:
    """List active experiments missing a snapshot for the given date (default today)."""
    engine = request.app.state.engine
    return list_snapshot_gaps(engine, snapshot_date=date)


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
        raise HTTPException(status_code=422, detail="event_type must not be empty")
    if not body.event_id.strip():
        raise HTTPException(status_code=422, detail="event_id must not be empty")

    ledger = get_ledger()
    event = ledger.append(body.event_type.strip(), body.event_id.strip(), body.payload)
    return {
        "logged": True,
        "event_type": event.event_type,
        "event_id": event.event_id,
        "created_at": event.created_at,
    }


class RecordMistakeRequest(BaseModel):
    category: str
    experiment_id: str
    summary: str
    lesson: str
    mistake_id: str | None = None
    tags: list[str] = Field(default_factory=list)


def _mistake_to_dict(record) -> dict:
    return {
        "mistake_id": record.mistake_id,
        "category": record.category,
        "experiment_id": record.experiment_id,
        "summary": record.summary,
        "lesson": record.lesson,
        "source": record.source,
        "created_at": record.created_at,
        "tags": list(record.tags),
    }


@router.get("/mistakes")
def list_operator_mistakes(
    experiment_id: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    """Return recorded experiment lessons from logs/mistakes.jsonl."""
    tracker = get_mistake_tracker()
    records = tracker.list_mistakes(
        experiment_id=experiment_id,
        category=category,
        limit=limit,
    )
    return {
        "count": len(records),
        "mistakes": [_mistake_to_dict(r) for r in records],
    }


@router.post("/mistakes")
def record_operator_mistake(body: RecordMistakeRequest) -> dict:
    """Record a durable lesson so future experiments avoid the same mistake."""
    if body.category.strip().lower() not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"category must be one of {sorted(VALID_CATEGORIES)}",
        )
    tracker = get_mistake_tracker()
    try:
        record = tracker.append(
            category=body.category,
            experiment_id=body.experiment_id,
            summary=body.summary,
            lesson=body.lesson,
            mistake_id=body.mistake_id,
            tags=body.tags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    get_ledger().append(
        "mistake.recorded",
        record.mistake_id,
        {
            "experiment_id": record.experiment_id,
            "category": record.category,
            "summary": record.summary,
        },
    )
    return {"recorded": True, "mistake": _mistake_to_dict(record)}
