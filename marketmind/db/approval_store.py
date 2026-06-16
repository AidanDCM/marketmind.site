"""Slice 12: Approval persistence and workflow.

Provides CRUD + status-transition operations for ApprovalRow.
All methods accept an Engine and open their own session — callers
don't need to manage sessions directly.

Business rules enforced here:
- Only PENDING records can be approved or denied.
- AUTO_ALLOWED records can be queried but not manually approved.
- BLOCKED and DENIED records are terminal (no further transitions).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.engine import Engine

from ..schemas import ApprovalRecord, ApprovalStatus, RiskLevel
from .engine import session_scope
from .models import ApprovalRow


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _row_to_record(row: ApprovalRow) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=row.approval_id,
        action=row.action,
        risk_level=RiskLevel(row.risk_level),
        status=ApprovalStatus(row.status),
        summary=row.summary,
        expected_cost=row.expected_cost,
        rollback_plan=row.rollback_plan,
        reason=row.reason,
    )


def _record_to_row(record: ApprovalRecord) -> ApprovalRow:
    return ApprovalRow(
        approval_id=record.approval_id,
        action=record.action,
        risk_level=record.risk_level.value,
        status=record.status.value,
        summary=record.summary,
        expected_cost=record.expected_cost,
        rollback_plan=record.rollback_plan,
        reason=record.reason,
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def create_approval(engine: Engine, record: ApprovalRecord) -> ApprovalRecord:
    """Persist a new approval record. Raises ValueError if ID already exists."""
    with session_scope(engine) as session:
        existing = session.get(ApprovalRow, record.approval_id)
        if existing is not None:
            raise ValueError(f"Approval {record.approval_id!r} already exists.")
        row = _record_to_row(record)
        session.add(row)
    return record


def get_approval(engine: Engine, approval_id: str) -> ApprovalRecord | None:
    """Return the approval record for the given ID, or None if not found."""
    with session_scope(engine) as session:
        row = session.get(ApprovalRow, approval_id)
        if row is None:
            return None
        return _row_to_record(row)


def list_approvals(
    engine: Engine,
    status: ApprovalStatus | None = None,
) -> list[ApprovalRecord]:
    """Return all approvals, optionally filtered by status."""
    with session_scope(engine) as session:
        stmt = select(ApprovalRow)
        if status is not None:
            stmt = stmt.where(ApprovalRow.status == status.value)
        rows = session.scalars(stmt).all()
        return [_row_to_record(r) for r in rows]


def list_pending(engine: Engine) -> list[ApprovalRecord]:
    """Convenience wrapper: return all PENDING approvals."""
    return list_approvals(engine, status=ApprovalStatus.PENDING)


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


def _transition(
    engine: Engine,
    approval_id: str,
    new_status: ApprovalStatus,
    note: str,
) -> ApprovalRecord:
    with session_scope(engine) as session:
        row = session.get(ApprovalRow, approval_id)
        if row is None:
            raise KeyError(f"Approval {approval_id!r} not found.")
        current = ApprovalStatus(row.status)
        if current != ApprovalStatus.PENDING:
            raise ValueError(
                f"Only PENDING approvals can be transitioned. "
                f"Current status: {current.value!r}."
            )
        row.status = new_status.value
        row.approver_note = note
        row.updated_at = _now()
        return _row_to_record(row)


def approve(engine: Engine, approval_id: str, note: str = "") -> ApprovalRecord:
    """Approve a PENDING record. Only valid for PENDING → APPROVED."""
    return _transition(engine, approval_id, ApprovalStatus.APPROVED, note)


def deny(engine: Engine, approval_id: str, note: str = "") -> ApprovalRecord:
    """Deny a PENDING record. Only valid for PENDING → DENIED."""
    return _transition(engine, approval_id, ApprovalStatus.DENIED, note)
