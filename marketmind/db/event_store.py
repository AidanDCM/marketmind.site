"""Append-only audit event ledger (writer for the `events` table).

The `events` table has existed since Slice 11 but had no writer. This is the
append-only ledger the executor uses to record what it did, so every action
taken on an approved request leaves a durable, queryable trail.

Events are never updated or deleted — only appended and read back.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.engine import Engine

from .engine import session_scope
from .models import EventRow


def append_event(
    engine: Engine,
    event_type: str,
    event_id: str,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append one event to the ledger. Payload is JSON-serialized to TEXT."""
    with session_scope(engine) as session:
        session.add(
            EventRow(
                event_type=event_type,
                event_id=event_id,
                payload=json.dumps(payload or {}, sort_keys=True),
            )
        )


def list_events(engine: Engine, event_type: str | None = None) -> list[dict[str, Any]]:
    """Return all events (optionally filtered by type), oldest first."""
    with session_scope(engine) as session:
        stmt = select(EventRow).order_by(EventRow.id)
        if event_type is not None:
            stmt = stmt.where(EventRow.event_type == event_type)
        rows = session.scalars(stmt).all()
        return [
            {
                "id": r.id,
                "event_type": r.event_type,
                "event_id": r.event_id,
                "created_at": r.created_at,
                "payload": json.loads(r.payload),
            }
            for r in rows
        ]


def event_exists(engine: Engine, event_type: str, event_id: str) -> bool:
    """Return True if an event with this (type, id) has already been recorded."""
    with session_scope(engine) as session:
        count = session.scalar(
            select(func.count())
            .select_from(EventRow)
            .where(EventRow.event_type == event_type)
            .where(EventRow.event_id == event_id)
        )
        return bool(count)
