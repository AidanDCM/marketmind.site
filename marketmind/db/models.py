"""Slice 11: SQLAlchemy ORM models.

All timestamps are ISO-8601 strings stored as TEXT (SQLite-friendly).
JSON payloads (e.g. event.payload) are stored as TEXT and serialized/deserialized
by the store layer — not at the ORM level.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


class ApprovalRow(Base):
    """Persisted approval record (mirrors ApprovalRecord dataclass)."""

    __tablename__ = "approvals"

    approval_id: Mapped[str] = mapped_column(primary_key=True)
    action: Mapped[str]
    risk_level: Mapped[str]
    status: Mapped[str]
    summary: Mapped[str] = mapped_column(Text)
    expected_cost: Mapped[float] = mapped_column(default=0.0)
    rollback_plan: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(default=_now)
    updated_at: Mapped[str] = mapped_column(default=_now)
    approver_note: Mapped[str] = mapped_column(Text, default="")


class ExperimentRow(Base):
    """Header record for a live experiment (one per product under test)."""

    __tablename__ = "experiments"

    experiment_id: Mapped[str] = mapped_column(primary_key=True)
    product_name: Mapped[str]
    break_even_cac: Mapped[float]
    status: Mapped[str] = mapped_column(default="active")
    started_at: Mapped[str] = mapped_column(default=_now)
    ended_at: Mapped[str | None] = mapped_column(nullable=True)


class ExperimentSnapshotRow(Base):
    """One period of observed performance data for an experiment."""

    __tablename__ = "experiment_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[str]
    snapshot_date: Mapped[str]
    qualified_visits: Mapped[int] = mapped_column(default=0)
    orders: Mapped[int] = mapped_column(default=0)
    total_ad_spend: Mapped[float] = mapped_column(default=0.0)
    total_revenue: Mapped[float] = mapped_column(default=0.0)
    refund_count: Mapped[int] = mapped_column(default=0)
    actual_shipping_cost: Mapped[float] = mapped_column(default=0.0)
    planned_shipping_cost: Mapped[float] = mapped_column(default=0.0)
    add_to_cart_count: Mapped[int] = mapped_column(default=0)
    consecutive_losing_periods: Mapped[int] = mapped_column(default=0)
    budget_cap: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[str] = mapped_column(default=_now)


class EventRow(Base):
    """Append-only audit event (mirrors JsonlEventLedger schema)."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[str]
    event_id: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=_now)
    payload: Mapped[str] = mapped_column(Text, default="{}")


class ImportBatchRow(Base):
    """Slice 29: one persisted pull from a live source or CSV importer."""

    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str]           # e.g. "stripe_charges", "shopify_orders", "csv_orders"
    pulled_at: Mapped[str] = mapped_column(default=_now)
    total_rows: Mapped[int] = mapped_column(default=0)
    ok_count: Mapped[int] = mapped_column(default=0)
    review_count: Mapped[int] = mapped_column(default=0)
    rows_json: Mapped[str] = mapped_column(Text, default="[]")  # JSON array of ok row dicts
