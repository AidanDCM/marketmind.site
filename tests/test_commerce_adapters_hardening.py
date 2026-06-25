"""Phase B pass 5 + rotation 2 pass 4: commerce adapter hardening."""

from __future__ import annotations

import json
import logging
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from marketmind.adapters import stripe_client as stripe_mod
from marketmind.adapters.gmail_client import create_supplier_gmail_draft
from marketmind.adapters.shopify_adapter import build_product_draft
from marketmind.adapters.shopify_client import ShopifyClient, simulate_create_product_draft
from marketmind.adapters.stripe_adapter import build_payment_link_payload
from marketmind.adapters.stripe_client import StripeClient, simulate_create_payment_link
from marketmind.api.app import app
from marketmind.commerce_adapters_contract import (
    COMMERCE_ACTION_ALIASES,
    SECRET_MASK_VECTORS,
)
from marketmind.commerce_approval_policy import normalize_commerce_action
from marketmind.commerce_integrations import get_commerce_integration_status
from marketmind.db import approval_store
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.docs_contract import REPO_ROOT
from marketmind.executor import record_action_payload
from marketmind.integrations_status import get_integrations_status
from marketmind.logging_config import mask_secret
from marketmind.operator_health_contract import (
    SHOPIFY_LIVE_NOT_READY_WARNING,
    STRIPE_LIVE_NOT_READY_WARNING,
)
from marketmind.schemas import (
    ApprovalRecord,
    ApprovalStatus,
    OfferContext,
    PaymentLinkPayload,
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


# ---------------------------------------------------------------------------
# Phase B rotation 2 pass 4: contract, aliases, API paths, CLI
# ---------------------------------------------------------------------------


@pytest.fixture
def commerce_api_engine():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def commerce_api_client(commerce_api_engine):
    app.state.engine = commerce_api_engine
    with TestClient(app) as client:
        yield client
    app.state.engine = None


@pytest.mark.parametrize("vector", SECRET_MASK_VECTORS.values(), ids=SECRET_MASK_VECTORS.keys())
def test_secret_mask_contract_vectors_are_redacted(vector: str):
    masked = mask_secret(vector)
    assert "***REDACTED***" in masked
    for fragment in vector.split():
        if fragment.startswith(("sk_", "pk_", "whsec_", "shpat_", "Bearer")):
            assert fragment not in masked


def test_commerce_action_aliases_normalize_to_policy_targets():
    for queue_action, policy_action in COMMERCE_ACTION_ALIASES.items():
        assert normalize_commerce_action(queue_action) == policy_action


def test_shopify_admin_access_token_configured_without_primary_token(monkeypatch):
    monkeypatch.delenv("SHOPIFY_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ADMIN_ACCESS_TOKEN", _SHOPIFY_TOKEN)
    status = get_commerce_integration_status()
    assert status["shopify"]["configured"] is True
    _assert_no_secrets(json.dumps(status))


def test_api_readiness_commerce_snapshot_with_live_writes(
    monkeypatch, commerce_api_client, tmp_path,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MARKETMIND_ENABLE_LIVE_WRITES", "true")
    monkeypatch.setenv("STRIPE_API_KEY", _STRIPE_KEY)
    monkeypatch.setenv("MARKETMIND_STRIPE_DRY_RUN", "true")
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", _SHOPIFY_TOKEN)
    monkeypatch.setenv("MARKETMIND_SHOPIFY_READ_ONLY", "true")

    resp = commerce_api_client.get("/operator/readiness")
    assert resp.status_code == 200
    body = resp.text
    _assert_no_secrets(body)
    data = resp.json()
    assert data["commerce"]["stripe"]["configured"] is True
    assert data["commerce"]["stripe"]["live_ready"] is False
    assert data["commerce"]["shopify"]["live_ready"] is False

    health = commerce_api_client.get("/operator/health-panel").json()
    assert STRIPE_LIVE_NOT_READY_WARNING in health["warnings"]
    assert SHOPIFY_LIVE_NOT_READY_WARNING in health["warnings"]


def test_api_execute_and_log_never_expose_stripe_key(
    commerce_api_client, commerce_api_engine, monkeypatch,
):
    monkeypatch.setenv("STRIPE_API_KEY", _STRIPE_KEY)

    def fake_post(self_inner, path, data):
        if path == "/products":
            return {"id": "prod_x"}
        if path == "/prices":
            return {"id": "price_x"}
        return {"id": "plink_api_x", "object": "payment_link", "url": "https://buy.stripe.com/x"}

    monkeypatch.setattr(stripe_mod.StripeClient, "_post", fake_post)

    approval_store.create_approval(
        commerce_api_engine,
        ApprovalRecord(
            approval_id="apr_stripe_hard",
            action="create_stripe_payment_link",
            risk_level=RiskLevel.HIGH,
            status=ApprovalStatus.PENDING,
            summary="Create payment link",
            expected_cost=59.0,
            rollback_plan="Delete via Stripe dashboard.",
        ),
    )
    record_action_payload(
        commerce_api_engine,
        "apr_stripe_hard",
        PaymentLinkPayload(product_name="Interior Kit", unit_amount_cents=5900).to_dict(),
    )
    approval_store.approve(commerce_api_engine, "apr_stripe_hard")

    resp = commerce_api_client.post("/execute/apr_stripe_hard", json={"dry_run": False})
    assert resp.status_code == 200
    _assert_no_secrets(resp.text)

    log_resp = commerce_api_client.get("/execute/log")
    assert log_resp.status_code == 200
    _assert_no_secrets(log_resp.text)


def test_check_commerce_config_script_stdout_has_no_secrets(monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", _STRIPE_KEY)
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", _SHOPIFY_TOKEN)
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_commerce_config.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    _assert_no_secrets(proc.stdout)
    assert "'configured': True" in proc.stdout or '"configured": true' in proc.stdout.lower()
