"""Slice 19: approved-action executor tests."""

import pytest

from marketmind.db import approval_store
from marketmind.db.engine import make_engine
from marketmind.db.event_store import append_event, event_exists, list_events
from marketmind.db.models import Base
from marketmind.executor import (
    execute_all_approved,
    execute_approved,
    execution_log,
)
from marketmind.schemas import ApprovalRecord, ApprovalStatus, RiskLevel


@pytest.fixture
def engine():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


def _scale_record(approval_id="apr_scale_x", status=ApprovalStatus.APPROVED) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=approval_id,
        action="scale_campaign",
        risk_level=RiskLevel.HIGH,
        status=status,
        summary="Scale request for Interior Kit",
        expected_cost=200.0,
        rollback_plan="Revert budget; pause if CAC rises.",
    )


# ---------------------------------------------------------------------------
# Event store
# ---------------------------------------------------------------------------


def test_event_store_roundtrip(engine):
    append_event(engine, "action_executed", "apr_1", {"k": "v"})
    events = list_events(engine, event_type="action_executed")
    assert len(events) == 1
    assert events[0]["event_id"] == "apr_1"
    assert events[0]["payload"] == {"k": "v"}
    assert event_exists(engine, "action_executed", "apr_1")
    assert not event_exists(engine, "action_executed", "apr_missing")


# ---------------------------------------------------------------------------
# Gate enforcement
# ---------------------------------------------------------------------------


def test_refuses_missing_approval(engine):
    with pytest.raises(KeyError):
        execute_approved(engine, "nope")


def test_refuses_pending(engine):
    approval_store.create_approval(engine, _scale_record(status=ApprovalStatus.PENDING))
    with pytest.raises(ValueError, match="not 'approved'"):
        execute_approved(engine, "apr_scale_x")


def test_refuses_denied(engine):
    approval_store.create_approval(engine, _scale_record(status=ApprovalStatus.DENIED))
    with pytest.raises(ValueError, match="not 'approved'"):
        execute_approved(engine, "apr_scale_x")


# ---------------------------------------------------------------------------
# Dry-run execution
# ---------------------------------------------------------------------------


def test_dry_run_executes_and_records_event(engine):
    approval_store.create_approval(engine, _scale_record())
    result = execute_approved(engine, "apr_scale_x", dry_run=True)
    assert result.executed is True
    assert result.dry_run is True
    assert result.detail["approved_budget"] == 200.0
    # Audit event recorded.
    assert event_exists(engine, "action_executed", "apr_scale_x")
    assert len(execution_log(engine)) == 1


def test_execution_is_idempotent(engine):
    approval_store.create_approval(engine, _scale_record())
    first = execute_approved(engine, "apr_scale_x")
    second = execute_approved(engine, "apr_scale_x")
    assert first.executed is True
    assert second.executed is False
    assert second.reason == "already_executed"
    assert len(execution_log(engine)) == 1  # not duplicated


# ---------------------------------------------------------------------------
# Live execution is refused (safe-fail)
# ---------------------------------------------------------------------------


def test_live_scale_is_refused(engine):
    approval_store.create_approval(engine, _scale_record())
    with pytest.raises(ValueError, match="no ad-platform integration"):
        execute_approved(engine, "apr_scale_x", dry_run=False)
    # Nothing recorded since it refused.
    assert not event_exists(engine, "action_executed", "apr_scale_x")


# ---------------------------------------------------------------------------
# Unknown action -> recorded as not executed, no error
# ---------------------------------------------------------------------------


def test_unknown_action_not_executed(engine):
    rec = ApprovalRecord(
        approval_id="apr_unknown",
        action="some_future_action",
        risk_level=RiskLevel.MEDIUM,
        status=ApprovalStatus.APPROVED,
        summary="future",
    )
    approval_store.create_approval(engine, rec)
    result = execute_approved(engine, "apr_unknown")
    assert result.executed is False
    assert "no executor registered" in result.reason


# ---------------------------------------------------------------------------
# Batch execution
# ---------------------------------------------------------------------------


def test_execute_all_approved_batch(engine):
    approval_store.create_approval(engine, _scale_record("apr_a"))
    approval_store.create_approval(engine, _scale_record("apr_b"))
    # A pending one should be ignored by the batch (only APPROVED are processed).
    approval_store.create_approval(
        engine, _scale_record("apr_pending", status=ApprovalStatus.PENDING)
    )

    results = execute_all_approved(engine, dry_run=True)
    executed_ids = {r.approval_id for r in results if r.executed}
    assert executed_ids == {"apr_a", "apr_b"}
    assert len(execution_log(engine)) == 2


def test_execute_all_captures_refusals(engine):
    approval_store.create_approval(engine, _scale_record("apr_live"))
    results = execute_all_approved(engine, dry_run=False)
    assert len(results) == 1
    assert results[0].executed is False
    assert "no ad-platform integration" in results[0].reason
