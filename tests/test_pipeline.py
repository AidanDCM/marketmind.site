"""Slice 21: offer -> approval pipeline tests (incl. end-to-end execute)."""

import pytest

from marketmind.db import approval_store
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.executor import execute_approved
from marketmind.pipeline import prepare_offer_for_approval
from marketmind.schemas import ApprovalStatus, OfferContext


@pytest.fixture
def engine():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


def _ctx() -> OfferContext:
    return OfferContext(
        product_name="Interior Refresh Kit",
        sale_price=59.0,
        key_benefit="Make your car feel new again",
        target_customer="daily commuters",
        secondary_benefits=("Easy 10-minute application",),
        common_objections=("Will it damage my dashboard?",),
    )


def test_unknown_channel_raises(engine):
    with pytest.raises(ValueError, match="Unknown channel"):
        prepare_offer_for_approval(engine, _ctx(), channel="ebay")


def test_stripe_offer_creates_pending_high_approval(engine):
    record = prepare_offer_for_approval(engine, _ctx(), channel="stripe")
    assert record.action == "create_stripe_payment_link"
    assert record.status == ApprovalStatus.PENDING
    assert record.risk_level.value == "high"
    assert record.expected_cost == 59.0
    # Persisted and retrievable.
    assert approval_store.get_approval(engine, record.approval_id) is not None


def test_shopify_offer_creates_pending_high_approval(engine):
    record = prepare_offer_for_approval(engine, _ctx(), channel="shopify")
    assert record.action == "publish_shopify_product"
    assert record.status == ApprovalStatus.PENDING


def test_stripe_end_to_end_prepare_approve_execute(engine):
    # Prepare: offer -> payload + PENDING approval
    record = prepare_offer_for_approval(engine, _ctx(), channel="stripe")
    # Human approves
    approval_store.approve(engine, record.approval_id, note="Looks good.")
    # Executor runs it (dry-run): payload was attached by the pipeline
    result = execute_approved(engine, record.approval_id, dry_run=True)
    assert result.executed is True
    assert result.detail["kind"] == "stripe_payment_link"
    assert result.detail["simulated"] is True
    assert result.detail["id"].startswith("plink_simulated_")


def test_shopify_end_to_end_prepare_approve_execute(engine):
    record = prepare_offer_for_approval(engine, _ctx(), channel="shopify")
    approval_store.approve(engine, record.approval_id)
    result = execute_approved(engine, record.approval_id, dry_run=True)
    assert result.executed is True
    assert result.detail["kind"] == "shopify_product"
    assert result.detail["simulated"] is True


def test_execute_before_approval_is_refused(engine):
    # A freshly prepared offer is PENDING; executing it must be refused.
    record = prepare_offer_for_approval(engine, _ctx(), channel="stripe")
    with pytest.raises(ValueError, match="not 'approved'"):
        execute_approved(engine, record.approval_id, dry_run=True)
