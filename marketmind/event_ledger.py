"""Append-only JSONL event ledger for MarketMind operator audit trail.

Adapted from Parts-and-Pieces `parts/python/event_ledger`.

Writes one JSON object per line to `logs/operator_events.jsonl`. Every
significant operator decision — approval, kill, scale, note, preflight check —
should be recorded here so the full operator history is replayable.

Usage:
    from marketmind.event_ledger import get_ledger
    ledger = get_ledger()
    ledger.append("experiment.killed", "kill-exp_001-20260623", {
        "experiment_id": "exp_001",
        "reason": "CAC exceeded break-even for 3 consecutive periods",
    })
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_PATH = Path("logs/operator_events.jsonl")


@dataclass(frozen=True)
class LedgerEvent:
    event_type: str
    event_id: str
    created_at: str
    payload: dict[str, Any]


class JsonlEventLedger:
    """Append-only JSONL event ledger.

    Each line is a complete JSON object. Reads are tolerant of partial lines
    and JSON errors (they are skipped, not raised). The ledger never deletes
    or rewrites entries — corrections are new entries.
    """

    def __init__(self, path: str | Path = _DEFAULT_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, event_id: str, payload: dict[str, Any]) -> LedgerEvent:
        event = LedgerEvent(
            event_type=event_type,
            event_id=event_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            payload=payload,
        )
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(event), sort_keys=True, default=str) + "\n")
        return event

    def read_all(self) -> list[LedgerEvent]:
        if not self.path.exists():
            return []
        events: list[LedgerEvent] = []
        with self.path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    events.append(_parse_line(json.loads(line)))
                except json.JSONDecodeError:
                    continue
        return events

    def read_tail(self, max_lines: int = 500) -> list[LedgerEvent]:
        if not self.path.exists():
            return []
        try:
            with self.path.open("rb") as fh:
                fh.seek(0, 2)
                size = fh.tell()
                chunk, data, pos = 65_536, b"", size
                while pos > 0 and data.count(b"\n") <= max_lines:
                    read_size = min(chunk, pos)
                    pos -= read_size
                    fh.seek(pos)
                    data = fh.read(read_size) + data
            lines = data.decode("utf-8", errors="replace").splitlines()[-max_lines:]
        except OSError:
            return []
        events: list[LedgerEvent] = []
        for line in lines:
            if not line.strip():
                continue
            try:
                events.append(_parse_line(json.loads(line)))
            except json.JSONDecodeError:
                continue
        return events


def _parse_line(raw: dict[str, Any]) -> LedgerEvent:
    if {"event_type", "event_id", "created_at", "payload"} <= set(raw):
        return LedgerEvent(**raw)
    event_type = str(raw.get("event_type", "unknown"))
    fallback = hashlib.sha256(
        json.dumps(raw, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]
    created_at = str(
        raw.get("created_at") or datetime.now(timezone.utc).isoformat()
    )
    payload = {k: v for k, v in raw.items() if k not in {"event_type", "event_id", "created_at"}}
    return LedgerEvent(
        event_type=event_type,
        event_id=str(raw.get("event_id") or f"{event_type}-{fallback}"),
        created_at=created_at,
        payload=payload,
    )


_ledger: JsonlEventLedger | None = None


def get_ledger(path: str | Path = _DEFAULT_PATH) -> JsonlEventLedger:
    """Return the shared ledger instance (lazy singleton)."""
    global _ledger
    if _ledger is None or Path(_ledger.path) != Path(path):
        _ledger = JsonlEventLedger(path)
    return _ledger
