"""Slice 12: Approval store tests."""

import pytest

from marketmind.db.approval_store import (
    approve,
    create_approval,
    deny,
    get_approval,
    list_approvals,
    list_pending,
)
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.schemas import ApprovalRecord, ApprovalStatus, RiskLevel


@pytest.fixture
def engine():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng


def _record(
    approval_id: str = "apr_001",
    status: ApprovalStatus = ApprovalStatus.PENDING,
    risk_level: RiskLevel = RiskLevel.HIGH,
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=approval_id,
        action="create_stripe_payment_link",
        risk_level=risk_level,
        status=status,
        summary="Create payment link for Interior Kit",
        expected_cost=59.0,
        rollback_plan="Delete link via Stripe dashboard.",
    )


# ---------------------------------------------------------------------------
# create / get
# ---------------------------------------------------------------------------


def test_create_and_get(engine):
    rec = _record()
    create_approval(engine, rec)
    retrieved = get_approval(engine, "apr_001")
    assert retrieved is not None
    assert retrieved.approval_id == "apr_001"
    assert retrieved.action == "create_stripe_payment_link"


def test_get_returns_none_for_missing(engine):
    assert get_approval(engine, "nonexistent") is None


def test_create_duplicate_raises(engine):
    create_approval(engine, _record())
    with pytest.raises(ValueError, match="already exists"):
        create_approval(engine, _record())


def test_create_preserves_risk_level(engine):
    create_approval(engine, _record(risk_level=RiskLevel.HIGH))
    retrieved = get_approval(engine, "apr_001")
    assert retrieved.risk_level == RiskLevel.HIGH


# ---------------------------------------------------------------------------
# list_approvals / list_pending
# ---------------------------------------------------------------------------


def test_list_pending_returns_only_pending(engine):
    create_approval(engine, _record("apr_001", ApprovalStatus.PENDING))
    create_approval(engine, _record("apr_002", ApprovalStatus.AUTO_ALLOWED, RiskLevel.LOW))
    pending = list_pending(engine)
    assert len(pending) == 1
    assert pending[0].approval_id == "apr_001"


def test_list_all_returns_all(engine):
    create_approval(engine, _record("apr_001", ApprovalStatus.PENDING))
    create_approval(engine, _record("apr_002", ApprovalStatus.AUTO_ALLOWED, RiskLevel.LOW))
    all_records = list_approvals(engine)
    assert len(all_records) == 2


def test_list_filter_by_status(engine):
    create_approval(engine, _record("apr_001", ApprovalStatus.PENDING))
    create_approval(engine, _record("apr_002", ApprovalStatus.AUTO_ALLOWED, RiskLevel.LOW))
    auto = list_approvals(engine, status=ApprovalStatus.AUTO_ALLOWED)
    assert len(auto) == 1
    assert auto[0].approval_id == "apr_002"


# ---------------------------------------------------------------------------
# approve
# ---------------------------------------------------------------------------


def test_approve_pending_record(engine):
    create_approval(engine, _record())
    result = approve(engine, "apr_001", note="Looks good.")
    assert result.status == ApprovalStatus.APPROVED


def test_approve_updates_status_in_db(engine):
    create_approval(engine, _record())
    approve(engine, "apr_001")
    retrieved = get_approval(engine, "apr_001")
    assert retrieved.status == ApprovalStatus.APPROVED


def test_approve_nonexistent_raises(engine):
    with pytest.raises(KeyError):
        approve(engine, "no_such_id")


def test_approve_already_approved_raises(engine):
    create_approval(engine, _record())
    approve(engine, "apr_001")
    with pytest.raises(ValueError, match="Only PENDING"):
        approve(engine, "apr_001")


# ---------------------------------------------------------------------------
# deny
# ---------------------------------------------------------------------------


def test_deny_pending_record(engine):
    create_approval(engine, _record())
    result = deny(engine, "apr_001", note="Not ready.")
    assert result.status == ApprovalStatus.DENIED


def test_deny_updates_status_in_db(engine):
    create_approval(engine, _record())
    deny(engine, "apr_001")
    retrieved = get_approval(engine, "apr_001")
    assert retrieved.status == ApprovalStatus.DENIED


def test_deny_nonexistent_raises(engine):
    with pytest.raises(KeyError):
        deny(engine, "no_such_id")


def test_deny_after_approve_raises(engine):
    create_approval(engine, _record())
    approve(engine, "apr_001")
    with pytest.raises(ValueError, match="Only PENDING"):
        deny(engine, "apr_001")
