"""Order lifecycle view — normalize Stripe/Shopify import rows into stages.

Adapted from Parts-and-Pieces `parts/typescript/order-lifecycle` concept.
Read-only: builds a pipeline view from persisted import batches.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .db.models import ImportBatchRow

_ORDER_SOURCES = frozenset({
    "stripe_charges",
    "shopify_orders",
    "stripe_webhook",
    "shopify_webhook",
})


@dataclass(frozen=True)
class OrderLifecycleEntry:
    order_id: str
    source: str
    stage: str
    amount: str
    currency: str
    raw_status: str
    batch_id: int
    pulled_at: str

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "source": self.source,
            "stage": self.stage,
            "amount": self.amount,
            "currency": self.currency,
            "raw_status": self.raw_status,
            "batch_id": self.batch_id,
            "pulled_at": self.pulled_at,
        }


def classify_order_stage(source: str, row: dict[str, str]) -> tuple[str, str]:
    """Return (stage, raw_status) from a normalized import row."""
    status = (
        row.get("status")
        or row.get("financial_status")
        or row.get("fulfillment_status")
        or row.get("event_type")
        or ""
    ).lower()
    raw = status or "unknown"

    if any(x in status for x in ("refund", "refunded", "charge.refunded")):
        return "refunded", raw
    if any(x in status for x in ("cancel", "void", "failed")):
        return "cancelled", raw
    if any(x in status for x in ("fulfill", "shipped", "delivered")):
        return "fulfilled", raw
    if any(x in status for x in ("paid", "succeeded", "complete", "captured")):
        return "paid", raw
    if any(x in status for x in ("pending", "open", "unpaid", "authorized")):
        return "placed", raw
    if "shopify" in source:
        return "placed", raw
    return "unknown", raw


def _order_id_from_row(source: str, row: dict[str, str]) -> str:
    for key in ("order_id", "id", "object_id", "name", "number"):
        val = row.get(key, "").strip()
        if val:
            return val
    return f"{source}-{row.get('event_id', 'unknown')}"


def build_order_lifecycle(engine: Engine, *, limit_batches: int = 30) -> list[OrderLifecycleEntry]:
    """Build a de-duplicated order lifecycle list from recent import batches."""
    entries: dict[str, OrderLifecycleEntry] = {}

    with Session(engine) as session:
        batches = session.scalars(
            select(ImportBatchRow)
            .where(ImportBatchRow.source.in_(_ORDER_SOURCES))
            .order_by(ImportBatchRow.id.desc())
            .limit(limit_batches)
        ).all()

        for batch in reversed(batches):
            try:
                rows = json.loads(batch.rows_json or "[]")
            except json.JSONDecodeError:
                continue
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                norm = {str(k).lower(): str(v) for k, v in row.items()}
                order_id = _order_id_from_row(batch.source, norm)
                stage, raw = classify_order_stage(batch.source, norm)
                entries[order_id] = OrderLifecycleEntry(
                    order_id=order_id,
                    source=batch.source,
                    stage=stage,
                    amount=norm.get("amount", norm.get("total_price", "")),
                    currency=norm.get("currency", ""),
                    raw_status=raw,
                    batch_id=batch.id,
                    pulled_at=batch.pulled_at,
                )

    return sorted(entries.values(), key=lambda e: e.pulled_at, reverse=True)
