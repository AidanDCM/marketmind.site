"""Slice 19: approved-action executor tests."""

from pathlib import Path

import pytest

from marketmind.adapters import stripe_client as stripe_mod
from marketmind.db import approval_store
from marketmind.db.engine import make_engine
from marketmind.db.event_store import append_event, event_exists, list_events
from marketmind.db.models import Base
from marketmind.executor import (
    execute_all_approved,
    execute_approved,
    execution_log,
    record_action_payload,
)
from marketmind.schemas import (
    ApprovalRecord,
    ApprovalStatus,
    PaymentLinkPayload,
    ProductDraftPayload,
    RiskLevel,
    ShopifyVariant,
)


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
    with pytest.raises(ValueError, match="reviewed before automation"):
        execute_approved(engine, "apr_unknown")


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


# ---------------------------------------------------------------------------
# Adapter-backed actions (Slice 20): Stripe + Shopify, payload via ledger
# ---------------------------------------------------------------------------


def _stripe_record(approval_id="apr_stripe") -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=approval_id,
        action="create_stripe_payment_link",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.APPROVED,
        summary="Create payment link for Interior Kit",
        expected_cost=59.0,
        rollback_plan="Deactivate the link in Stripe.",
    )


def _shopify_record(approval_id="apr_shopify") -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=approval_id,
        action="publish_shopify_product",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.APPROVED,
        summary="Publish Interior Kit draft",
        expected_cost=1.0,
        rollback_plan="Set product back to draft.",
    )


def test_stripe_dry_run_uses_simulate(engine):
    approval_store.create_approval(engine, _stripe_record())
    payload = PaymentLinkPayload(product_name="Interior Kit", unit_amount_cents=5900)
    record_action_payload(engine, "apr_stripe", payload.to_dict())

    result = execute_approved(engine, "apr_stripe", dry_run=True)
    assert result.executed is True
    assert result.detail["simulated"] is True
    assert result.detail["id"].startswith("plink_simulated_")


def test_stripe_missing_payload_refused(engine):
    approval_store.create_approval(engine, _stripe_record())
    # execute_approved raises on refusal; the batch variant captures it instead.
    with pytest.raises(ValueError, match="No payload recorded"):
        execute_approved(engine, "apr_stripe", dry_run=True)
    results = execute_all_approved(engine, dry_run=True)
    assert results[0].executed is False
    assert "No payload recorded" in results[0].reason


def test_stripe_live_without_key_refused(engine, monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    approval_store.create_approval(engine, _stripe_record())
    payload = PaymentLinkPayload(product_name="Interior Kit", unit_amount_cents=5900)
    record_action_payload(engine, "apr_stripe", payload.to_dict())
    with pytest.raises(ValueError, match="STRIPE_API_KEY"):
        execute_approved(engine, "apr_stripe", dry_run=False)


def test_stripe_live_with_mocked_client(engine, monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", "sk_test_dummy")

    def fake_post(self_inner, path, data):
        if path == "/products":
            return {"id": "prod_x"}
        if path == "/prices":
            return {"id": "price_x"}
        return {"id": "plink_live_x", "object": "payment_link", "url": "https://buy.stripe.com/x"}

    monkeypatch.setattr(stripe_mod.StripeClient, "_post", fake_post)
    approval_store.create_approval(engine, _stripe_record())
    payload = PaymentLinkPayload(product_name="Interior Kit", unit_amount_cents=5900)
    record_action_payload(engine, "apr_stripe", payload.to_dict())

    result = execute_approved(engine, "apr_stripe", dry_run=False)
    assert result.executed is True
    assert result.detail["simulated"] is False
    assert result.detail["id"] == "plink_live_x"
    # The secret never leaks into the result.
    assert "sk_test_dummy" not in str(result.to_dict())


def test_shopify_dry_run_uses_simulate(engine):
    approval_store.create_approval(engine, _shopify_record())
    payload = ProductDraftPayload(
        title="Interior Kit",
        body_html="<p>Clean interior fast</p>",
        vendor="MarketMind",
        product_type="Auto Accessory",
        variants=(ShopifyVariant(price="59.00", sku="IK-1"),),
    )
    record_action_payload(engine, "apr_shopify", payload.to_dict())

    result = execute_approved(engine, "apr_shopify", dry_run=True)
    assert result.executed is True
    assert result.detail["simulated"] is True
    assert result.detail["id"] == "simulated_apr_shopify"


def test_shopify_live_without_creds_refused(engine, monkeypatch):
    monkeypatch.delenv("SHOPIFY_STORE_DOMAIN", raising=False)
    monkeypatch.delenv("SHOPIFY_ACCESS_TOKEN", raising=False)
    approval_store.create_approval(engine, _shopify_record())
    payload = ProductDraftPayload(
        title="Interior Kit", body_html="x", vendor="MM", product_type="Auto",
        variants=(ShopifyVariant(price="59.00"),),
    )
    record_action_payload(engine, "apr_shopify", payload.to_dict())
    with pytest.raises(ValueError, match="SHOPIFY_STORE_DOMAIN"):
        execute_approved(engine, "apr_shopify", dry_run=False)


def test_contact_supplier_dry_run_exports_draft_file(engine, tmp_path, monkeypatch):
    from marketmind import gmail_draft
    from marketmind.pipeline import prepare_supplier_outreach_for_approval

    real_save = gmail_draft.save_outreach_draft_file

    def _save(**kwargs):
        kwargs.setdefault("output_dir", tmp_path)
        return real_save(**kwargs)

    monkeypatch.setattr(gmail_draft, "save_outreach_draft_file", _save)

    record = prepare_supplier_outreach_for_approval(
        engine,
        supplier_name="Acme",
        product_name="Interior Kit",
        expected_cost=20.0,
    )
    approval_store.approve(engine, record.approval_id)
    result = execute_approved(engine, record.approval_id, dry_run=True)
    assert result.detail["simulated"] is True
    draft_path = Path(result.detail["draft_file"])
    assert draft_path.exists()
    assert "Interior Kit" in draft_path.read_text(encoding="utf-8")
