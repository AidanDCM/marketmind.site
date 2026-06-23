"""Append-only mistake / lesson tracker for MarketMind experiments.

Adapted from Parts-and-Pieces `parts/python/mistake_tracker`.

Records durable lessons from failed or paused experiments so the operator
does not repeat losing patterns. Stored at ``logs/mistakes.jsonl`` (append-only).
Auto-suggestions are derived from experiment rulings and risks but are not
written until the operator confirms them via ``POST /operator/mistakes``.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_PATH = Path("logs/mistakes.jsonl")

VALID_CATEGORIES = frozenset({
    "cac_too_high",
    "low_conversion",
    "high_refunds",
    "offer_miss",
    "shipping_overrun",
    "other",
})


@dataclass(frozen=True)
class MistakeRecord:
    mistake_id: str
    category: str
    experiment_id: str
    summary: str
    lesson: str
    source: str
    created_at: str
    tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MistakeSuggestion:
    category: str
    experiment_id: str
    summary: str
    lesson: str
    source: str
    tags: tuple[str, ...] = field(default_factory=tuple)


class JsonlMistakeTracker:
    """Append-only JSONL store for operator-recorded experiment lessons."""

    def __init__(self, path: str | Path = _DEFAULT_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        *,
        category: str,
        experiment_id: str,
        summary: str,
        lesson: str,
        source: str = "manual",
        mistake_id: str | None = None,
        tags: list[str] | None = None,
    ) -> MistakeRecord:
        cat = category.strip().lower()
        if cat not in VALID_CATEGORIES:
            raise ValueError(
                f"category must be one of {sorted(VALID_CATEGORIES)}, got {category!r}"
            )
        if not experiment_id.strip():
            raise ValueError("experiment_id must not be empty")
        if not summary.strip():
            raise ValueError("summary must not be empty")
        if not lesson.strip():
            raise ValueError("lesson must not be empty")

        record = MistakeRecord(
            mistake_id=mistake_id.strip() if mistake_id and mistake_id.strip() else _new_id(),
            category=cat,
            experiment_id=experiment_id.strip(),
            summary=summary.strip(),
            lesson=lesson.strip(),
            source=source.strip() or "manual",
            created_at=datetime.now(timezone.utc).isoformat(),
            tags=tuple(t.strip() for t in (tags or []) if t.strip()),
        )
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record), sort_keys=True) + "\n")
        return record

    def read_all(self) -> list[MistakeRecord]:
        if not self.path.exists():
            return []
        records: list[MistakeRecord] = []
        with self.path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    records.append(_parse_line(json.loads(line)))
                except (json.JSONDecodeError, ValueError, TypeError):
                    continue
        return records

    def list_mistakes(
        self,
        *,
        experiment_id: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[MistakeRecord]:
        items = self.read_all()
        if experiment_id:
            items = [m for m in items if m.experiment_id == experiment_id]
        if category:
            cat = category.strip().lower()
            items = [m for m in items if m.category == cat]
        return items[-limit:]


def _new_id() -> str:
    return f"mistake-{uuid.uuid4().hex[:12]}"


def _parse_line(raw: dict[str, Any]) -> MistakeRecord:
    tags = raw.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return MistakeRecord(
        mistake_id=str(raw["mistake_id"]),
        category=str(raw["category"]),
        experiment_id=str(raw["experiment_id"]),
        summary=str(raw["summary"]),
        lesson=str(raw["lesson"]),
        source=str(raw.get("source", "manual")),
        created_at=str(raw.get("created_at") or datetime.now(timezone.utc).isoformat()),
        tags=tuple(str(t) for t in tags),
    )


def suggest_mistakes(
    *,
    experiment_id: str,
    product_name: str,
    ruling: str | None,
    risks: list[str],
    note_bodies: list[str] | None = None,
) -> list[MistakeSuggestion]:
    """Derive lesson suggestions from a ruling and risk flags (not persisted)."""
    suggestions: list[MistakeSuggestion] = []
    seen: set[str] = set()
    risk_text = " ".join(risks).lower()

    def add(category: str, summary: str, lesson: str, tags: list[str]) -> None:
        key = f"{category}:{summary}"
        if key in seen:
            return
        seen.add(key)
        suggestions.append(MistakeSuggestion(
            category=category,
            experiment_id=experiment_id,
            summary=summary,
            lesson=lesson,
            source="auto_ruling",
            tags=tuple(tags),
        ))

    if ruling in {"kill", "pause_ads"}:
        add(
            "cac_too_high",
            f"{product_name}: ads became uneconomical",
            "Pause or kill before CAC exceeds break-even for multiple periods; "
            "revise targeting or offer before re-testing.",
            ["ruling", ruling or ""],
        )
    if ruling == "revise_offer":
        add(
            "offer_miss",
            f"{product_name}: offer did not convert",
            "Revise headline, price, or bundle before spending more on ads.",
            ["ruling", "revise_offer"],
        )
    if "refund" in risk_text:
        add(
            "high_refunds",
            f"{product_name}: refund rate flagged",
            "Investigate product quality and listing accuracy before scaling spend.",
            ["risk", "refunds"],
        )
    if "shipping" in risk_text:
        add(
            "shipping_overrun",
            f"{product_name}: shipping cost overrun",
            "Re-quote shipping or adjust price before the next test batch.",
            ["risk", "shipping"],
        )
    if "conversion" in risk_text or "add-to-cart" in risk_text or "atc" in risk_text:
        add(
            "low_conversion",
            f"{product_name}: weak funnel metrics",
            "Test creative, landing page, and price before increasing ad budget.",
            ["risk", "conversion"],
        )

    for body in note_bodies or []:
        text = body.strip()
        if len(text) < 12:
            continue
        add(
            "other",
            f"{product_name}: operator note",
            text,
            ["note"],
        )

    return suggestions


_tracker: JsonlMistakeTracker | None = None


def get_mistake_tracker(path: str | Path = _DEFAULT_PATH) -> JsonlMistakeTracker:
    global _tracker
    if _tracker is None or Path(_tracker.path) != Path(path):
        _tracker = JsonlMistakeTracker(path)
    return _tracker
