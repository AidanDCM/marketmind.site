"""Slice 17: ShopifyClient tests (mocked HTTP)."""

import pytest

from marketmind.adapters.shopify_adapter import build_product_draft
from marketmind.adapters.shopify_client import (
    ShopifyClient,
    _assert_approved,
    simulate_create_product_draft,
)
from marketmind.schemas import ApprovalRecord, ApprovalStatus, OfferContext, RiskLevel
from marketmind.spec_generator import generate_offer_spec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _approved() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_shopify_live",
        action="publish_shopify_product",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.APPROVED,
        summary="Create Shopify product draft",
        expected_cost=0.0,
        rollback_plan="Set back to draft in Shopify admin.",
    )


def _pending() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_shopify_pending",
        action="publish_shopify_product",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Pending product draft",
        expected_cost=0.0,
        rollback_plan="Set back to draft.",
    )


def _spec():
    ctx = OfferContext(
        product_name="Daily Driver Interior Refresh Kit",
        sale_price=59.0,
        key_benefit="Upgrade your car's interior feel",
        target_customer="daily commuters",
        secondary_benefits=("Microfiber cloth",),
        shipping_note="Ships in 3-5 days.",
        return_policy="30-day returns.",
    )
    return generate_offer_spec(ctx)


def _live_payload():
    return build_product_draft(_spec(), approval=_approved(), dry_run=False)


# ---------------------------------------------------------------------------
# ShopifyClient construction
# ---------------------------------------------------------------------------


def test_shopify_client_requires_domain():
    with pytest.raises(ValueError, match="store_domain is required"):
        ShopifyClient("", "shpat_token")


def test_shopify_client_requires_token():
    with pytest.raises(ValueError, match="access_token is required"):
        ShopifyClient("mystore.myshopify.com", "")


def test_shopify_client_constructs():
    client = ShopifyClient("mystore.myshopify.com", "shpat_dummy")
    assert client is not None


# ---------------------------------------------------------------------------
# Gate enforcement
# ---------------------------------------------------------------------------


def test_assert_approved_raises_on_pending():
    with pytest.raises(ValueError, match="status=APPROVED"):
        _assert_approved(_pending(), "create_product_draft")


def test_assert_approved_raises_on_wrong_risk():
    low_risk = ApprovalRecord(
        approval_id="apr_low",
        action="score_product",
        risk_level=RiskLevel.LOW,
        status=ApprovalStatus.APPROVED,
        summary="Low risk",
    )
    with pytest.raises(ValueError, match="HIGH-risk"):
        _assert_approved(low_risk, "create_product_draft")


def test_create_product_draft_dry_run_flag_raises(monkeypatch):
    client = ShopifyClient("mystore.myshopify.com", "shpat_dummy")
    approval = _approved()
    dry_payload = build_product_draft(_spec(), approval=approval)
    assert dry_payload.dry_run is True
    with pytest.raises(ValueError, match="dry_run is True"):
        client.create_product_draft(dry_payload, approval)


# ---------------------------------------------------------------------------
# simulate_create_product_draft
# ---------------------------------------------------------------------------


def test_simulate_requires_approved_record():
    with pytest.raises(ValueError, match="status=APPROVED"):
        simulate_create_product_draft(_live_payload(), _pending())


def test_simulate_returns_fake_response():
    result = simulate_create_product_draft(_live_payload(), _approved())
    assert "product" in result
    assert result["product"]["status"] == "draft"
    assert result["product"]["_dry_run"] is True


def test_simulate_product_title_matches():
    result = simulate_create_product_draft(_live_payload(), _approved())
    assert result["product"]["title"] == "Daily Driver Interior Refresh Kit"


# ---------------------------------------------------------------------------
# Mocked live HTTP call
# ---------------------------------------------------------------------------


def test_create_product_draft_makes_post(monkeypatch):
    calls = []

    def fake_post(self_inner, path, body):
        calls.append(path)
        return {
            "product": {
                "id": "shopify_prod_001",
                "title": body["product"]["title"],
                "status": "draft",
            }
        }

    monkeypatch.setattr(ShopifyClient, "_post", fake_post)
    client = ShopifyClient("mystore.myshopify.com", "shpat_dummy")
    result = client.create_product_draft(_live_payload(), _approved())

    assert "/products.json" in calls
    assert result["product"]["id"] == "shopify_prod_001"
    assert result["product"]["status"] == "draft"


def test_access_token_not_in_response(monkeypatch):
    def fake_post(self_inner, path, body):
        return {"product": {"id": "p_001", "title": body["product"]["title"], "status": "draft"}}

    monkeypatch.setattr(ShopifyClient, "_post", fake_post)
    client = ShopifyClient("mystore.myshopify.com", "shpat_REALSECRETTOKEN")
    result = client.create_product_draft(_live_payload(), _approved())
    assert "shpat_REALSECRETTOKEN" not in str(result)


def test_product_always_created_as_draft(monkeypatch):
    posted_bodies = []

    def fake_post(self_inner, path, body):
        posted_bodies.append(body)
        return {"product": {"id": "p_001", "status": body["product"]["status"]}}

    monkeypatch.setattr(ShopifyClient, "_post", fake_post)
    client = ShopifyClient("mystore.myshopify.com", "shpat_dummy")
    client.create_product_draft(_live_payload(), _approved())
    assert posted_bodies[0]["product"]["status"] == "draft"
