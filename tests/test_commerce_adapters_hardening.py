"""Phase B pass 5: commerce adapter hardening — fakes and no secrets in logs/responses."""

from __future__ import annotations

import json
import logging

import pytest

from marketmind.adapters.gmail_client import create_supplier_gmail_draft
from marketmind.adapters.shopify_adapter import build_product_draft
from marketmind.adapters.shopify_client import ShopifyClient, simulate_create_product_draft
from marketmind.adapters.stripe_adapter import build_payment_link_payload
from marketmind.adapters.stripe_client import StripeClient, simulate_create_payment_link
from marketmind.commerce_integrations import get_commerce_integration_status
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.integrations_status import get_integrations_status
from marketmind.schemas import (
    ApprovalRecord,
    ApprovalStatus,
    OfferContext,
    RiskLevel,
)
from marketmind.spec_generator import generate_offer_spec

_STRIPE_KEY = "sk_test_SUPERSECRET_STRIPE_KEY_999"
_SHOPIFY_TOKEN = "shpat_SUPERSECRET_SHOPIFY_TOKEN_999"
_GMAIL_SECRET = "gmail_client_secret_SUPERSECRET"
_GMAIL_REFRESH = "refresh_token_SUPERSECRET_abc123"


def _approved_stripe() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_stripe_hard",
        action="create_stripe_payment_link",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.APPROVED,
        summary="Create payment link",
        expected_cost=59.0,
        rollback_plan="Delete via Stripe dashboard.",
    )


def _approved_shopify() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_shopify_hard",
        action="publish_shopify_product",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.APPROVED,
        summary="Create Shopify draft",
        expected_cost=0.0,
        rollback_plan="Set back to draft.",
    )


def _approved_gmail() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_gmail_hard",
        action="contact_supplier",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.APPROVED,
        summary="Contact supplier",
        expected_cost=0.0,
        rollback_plan="Discard draft",
    )


def _offer_spec():
    ctx = OfferContext(
        product_name="Daily Driver Interior Refresh Kit",
        sale_price=59.0,
        key_benefit="Upgrade your car's interior feel",
        target_customer="daily commuters",
    )
    return generate_offer_spec(ctx)


def _assert_no_secrets(text: str) -> None:
    for secret in (_STRIPE_KEY, _SHOPIFY_TOKEN, _GMAIL_SECRET, _GMAIL_REFRESH):
        assert secret not in text, f"Secret leaked into output: {secret[:8]}..."


# ---------------------------------------------------------------------------
# Readiness snapshots never echo credential values
# ---------------------------------------------------------------------------


def test_commerce_integration_status_never_exposes_credentials(monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", _STRIPE_KEY)
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", _SHOPIFY_TOKEN)
    status = get_commerce_integration_status()
    assert status["stripe"]["configured"] is True
    assert status["shopify"]["configured"] is True
    _assert_no_secrets(json.dumps(status))


def test_integrations_status_never_exposes_credentials(monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", _STRIPE_KEY)
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", _SHOPIFY_TOKEN)
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", _GMAIL_SECRET)
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", _GMAIL_REFRESH)
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    status = get_integrations_status(engine)
    assert status["gmail"]["wired"] is True
    _assert_no_secrets(json.dumps(status))


# ---------------------------------------------------------------------------
# Simulated adapter responses stay secret-free
# ---------------------------------------------------------------------------


def test_stripe_simulate_response_has_no_secrets():
    payload = build_payment_link_payload(
        _offer_spec(), approval=_approved_stripe(), dry_run=False
    )
    result = simulate_create_payment_link(payload, _approved_stripe())
    _assert_no_secrets(json.dumps(result))
    assert result["_dry_run"] is True


def test_shopify_simulate_response_has_no_secrets():
    payload = build_product_draft(_offer_spec(), approval=_approved_shopify(), dry_run=False)
    result = simulate_create_product_draft(payload, _approved_shopify())
    _assert_no_secrets(json.dumps(result))
    assert result["product"]["_dry_run"] is True


def test_shopify_payload_to_dict_has_no_secrets():
    payload = build_product_draft(_offer_spec(), approval=_approved_shopify(), dry_run=False)
    combined = json.dumps(payload.to_dict())
    assert "shpat_" not in combined
    assert "sk_" not in combined


# ---------------------------------------------------------------------------
# Client logs never contain API keys/tokens (even on DEBUG)
# ---------------------------------------------------------------------------


def test_stripe_client_logs_never_contain_api_key(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG, logger="marketmind.adapters.stripe_client")

    def fake_post(self_inner, path, data):
        if path == "/products":
            return {"id": "prod_x"}
        if path == "/prices":
            return {"id": "price_x"}
        return {"id": "plink_x", "object": "payment_link", "url": "https://buy.stripe.com/x"}

    monkeypatch.setattr(StripeClient, "_post", fake_post)
    payload = build_payment_link_payload(
        _offer_spec(), approval=_approved_stripe(), dry_run=False
    )
    client = StripeClient(_STRIPE_KEY)
    client.create_payment_link(payload, _approved_stripe())
    _assert_no_secrets(caplog.text)


def test_shopify_client_logs_never_contain_access_token(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG, logger="marketmind.adapters.shopify_client")

    def fake_post(self_inner, path, body):
        return {"product": {"id": "p_001", "title": body["product"]["title"], "status": "draft"}}

    monkeypatch.setattr(ShopifyClient, "_post", fake_post)
    payload = build_product_draft(_offer_spec(), approval=_approved_shopify(), dry_run=False)
    client = ShopifyClient("demo.myshopify.com", _SHOPIFY_TOKEN)
    client.create_product_draft(payload, _approved_shopify())
    _assert_no_secrets(caplog.text)


def test_gmail_simulate_logs_never_contain_refresh_token(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG, logger="marketmind.adapters.gmail_client")
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", _GMAIL_SECRET)
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", _GMAIL_REFRESH)
    result = create_supplier_gmail_draft(
        approval=_approved_gmail(),
        to_address="buyer@acme.example",
        subject="Sample inquiry",
        body="Hello supplier",
    )
    assert result["simulated"] is True
    _assert_no_secrets(caplog.text)
    _assert_no_secrets(json.dumps(result))


def test_gmail_simulate_rejects_pending_approval(monkeypatch):
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", _GMAIL_REFRESH)
    pending = ApprovalRecord(
        approval_id="apr_gmail_pending",
        action="contact_supplier",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Pending",
        expected_cost=0.0,
        rollback_plan="Discard",
    )
    with pytest.raises(ValueError, match="not approved"):
        create_supplier_gmail_draft(
            approval=pending,
            to_address="buyer@acme.example",
            subject="S",
            body="B",
        )
