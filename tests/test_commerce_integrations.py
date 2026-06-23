"""Slice 59: commerce integration readiness tests."""

from marketmind.commerce_integrations import get_commerce_integration_status


def test_commerce_integrations_defaults(monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    monkeypatch.delenv("STRIPE_RESTRICTED_KEY", raising=False)
    monkeypatch.delenv("SHOPIFY_STORE_DOMAIN", raising=False)
    status = get_commerce_integration_status()
    assert status["stripe"]["configured"] is False
    assert status["stripe"]["dry_run"] is True
    assert status["shopify"]["configured"] is False
    assert status["shopify"]["read_only"] is True


def test_commerce_integrations_live_ready(monkeypatch):
    monkeypatch.setenv("STRIPE_RESTRICTED_KEY", "rk_test_x")
    monkeypatch.setenv("MARKETMIND_STRIPE_DRY_RUN", "false")
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", "shpat_x")
    monkeypatch.setenv("MARKETMIND_SHOPIFY_READ_ONLY", "false")
    status = get_commerce_integration_status()
    assert status["stripe"]["live_ready"] is True
    assert status["shopify"]["live_ready"] is True
