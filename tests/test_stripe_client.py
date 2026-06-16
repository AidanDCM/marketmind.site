"""Slice 16: StripeClient tests (mocked HTTP)."""

import pytest

from marketmind.adapters.stripe_adapter import build_payment_link_payload
from marketmind.adapters.stripe_client import (
    StripeClient,
    _assert_approved,
    simulate_create_payment_link,
)
from marketmind.schemas import ApprovalRecord, ApprovalStatus, OfferContext, RiskLevel
from marketmind.spec_generator import generate_offer_spec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _approved() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_stripe_live",
        action="create_stripe_payment_link",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.APPROVED,
        summary="Create Payment Link",
        expected_cost=59.0,
        rollback_plan="Delete via Stripe dashboard.",
    )


def _pending() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_stripe_pending",
        action="create_stripe_payment_link",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Create Payment Link",
        expected_cost=59.0,
        rollback_plan="Delete via Stripe dashboard.",
    )


def _spec():
    ctx = OfferContext(
        product_name="Daily Driver Interior Refresh Kit",
        sale_price=59.0,
        key_benefit="Upgrade your car's interior feel",
        target_customer="daily commuters",
    )
    return generate_offer_spec(ctx)


def _live_payload():
    return build_payment_link_payload(_spec(), approval=_approved(), dry_run=False)


# ---------------------------------------------------------------------------
# StripeClient construction
# ---------------------------------------------------------------------------


def test_stripe_client_requires_api_key():
    with pytest.raises(ValueError, match="api_key is required"):
        StripeClient("")


def test_stripe_client_constructs_with_key():
    client = StripeClient("sk_test_dummy")
    assert client is not None


# ---------------------------------------------------------------------------
# Gate enforcement
# ---------------------------------------------------------------------------


def test_assert_approved_raises_on_pending():
    with pytest.raises(ValueError, match="status=APPROVED"):
        _assert_approved(_pending(), "test_op")


def test_assert_approved_raises_on_wrong_risk():
    low_risk = ApprovalRecord(
        approval_id="apr_low",
        action="score_product",
        risk_level=RiskLevel.LOW,
        status=ApprovalStatus.APPROVED,
        summary="Low risk",
    )
    with pytest.raises(ValueError, match="HIGH-risk"):
        _assert_approved(low_risk, "test_op")


def test_create_payment_link_dry_run_flag_raises(monkeypatch):
    client = StripeClient("sk_test_dummy")
    approval = _approved()
    dry_payload = build_payment_link_payload(_spec(), approval=approval)
    assert dry_payload.dry_run is True
    with pytest.raises(ValueError, match="dry_run is True"):
        client.create_payment_link(dry_payload, approval)


# ---------------------------------------------------------------------------
# simulate_create_payment_link (approval-gated dry-run)
# ---------------------------------------------------------------------------


def test_simulate_requires_approved_record():
    with pytest.raises(ValueError, match="status=APPROVED"):
        simulate_create_payment_link(_live_payload(), _pending())


def test_simulate_returns_fake_response():
    result = simulate_create_payment_link(_live_payload(), _approved())
    assert result["object"] == "payment_link"
    assert result["_dry_run"] is True
    assert "url" in result


def test_simulate_contains_product_name():
    result = simulate_create_payment_link(_live_payload(), _approved())
    assert "Daily" in result["url"] or "simulated" in result["id"]


# ---------------------------------------------------------------------------
# Mocked live HTTP call
# ---------------------------------------------------------------------------


def test_create_payment_link_makes_three_api_calls(monkeypatch):
    calls = []

    def fake_post(self_inner, path, data):
        calls.append(path)
        if path == "/products":
            return {"id": "prod_fake123"}
        if path == "/prices":
            return {"id": "price_fake456"}
        if path == "/payment_links":
            return {"id": "plink_fake789", "object": "payment_link", "url": "https://buy.stripe.com/fake"}
        return {}

    monkeypatch.setattr(StripeClient, "_post", fake_post)
    client = StripeClient("sk_test_dummy")
    result = client.create_payment_link(_live_payload(), _approved())

    assert "/products" in calls
    assert "/prices" in calls
    assert "/payment_links" in calls
    assert result["id"] == "plink_fake789"


def test_create_payment_link_zero_cents_raises():
    import dataclasses
    payload = dataclasses.replace(_live_payload(), unit_amount_cents=0)
    client = StripeClient("sk_test_dummy")
    with pytest.raises(ValueError, match="unit_amount_cents"):
        client.create_payment_link(payload, _approved())


def test_api_key_not_in_response(monkeypatch):
    def fake_post(self_inner, path, data):
        if path == "/products":
            return {"id": "prod_x"}
        if path == "/prices":
            return {"id": "price_x"}
        return {"id": "plink_x", "object": "payment_link", "url": "https://buy.stripe.com/x"}

    monkeypatch.setattr(StripeClient, "_post", fake_post)
    client = StripeClient("sk_live_REALSECRET999")
    result = client.create_payment_link(_live_payload(), _approved())
    assert "sk_live_REALSECRET999" not in str(result)
