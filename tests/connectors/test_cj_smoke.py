"""
Smoke tests for CJ adapter: health probe, idempotency behavior, and retry/backoff.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
import requests

from packages.connectors.channels.cj import CJAdapter, CJProduct


TEST_CONFIG = {
    "website_id": "12345678",
    "auth_token": "test_auth_token_123",
    "api_key": "test_api_key_456",
    "sandbox": True,
}


@pytest.fixture
def cj_adapter():
    with patch("requests.Session"):
        adapter = CJAdapter(config=TEST_CONFIG)
        # Seed a mock product so inventory update can target it
        adapter._mock_products = {
            "CJ-12345": CJProduct(
                sku="CJ-12345",
                title="Seed Product",
                description="Seed",
                price=10.0,
                quantity=1,
                cj_id="12345",
                advertiser_id="ADV123",
                advertiser_name="Advertiser",
                buy_url="https://example.com/buy/12345",
                image_url="https://example.com/images/12345.jpg",
                in_stock=True,
                category="Electronics",
                subcategory="Gadgets",
                last_updated=datetime.utcnow(),
            )
        }
        yield adapter


def test_health_ok(cj_adapter: CJAdapter):
    res = cj_adapter.health()
    assert res.get("ok") is True
    assert res.get("name") == CJAdapter.CHANNEL_NAME


def test_idempotent_update_inventory_single_effect(cj_adapter: CJAdapter):
    updates = [
        {"sku": "CJ-12345", "quantity": 7},
        {"sku": "CJ-NEW", "quantity": 2},
    ]

    # Patch print to ensure the function body only executes once due to idempotency caching
    with patch("builtins.print") as mock_print:
        assert cj_adapter.update_inventory(updates) is True
        # Second identical call should hit idempotency cache and not execute body
        assert cj_adapter.update_inventory(updates) is True
        # Only the first call should have produced log lines
        mock_print.assert_any_call("  ✓ Updated inventory for SKU CJ-12345 to 7")
        mock_print.assert_any_call("  ✓ Updated inventory for SKU CJ-NEW to 2")
        # Total calls should correspond to two SKUs only once
        assert mock_print.call_count == 2


def test_retry_backoff_on_request(cj_adapter: CJAdapter):
    # Exercise the @retryable on _make_request: fail twice, succeed third
    with patch.object(cj_adapter, "session") as mock_session:
        # Configure side effects: two RequestException then success JSON
        mock_session.request.side_effect = [
            requests.exceptions.RequestException("net down"),
            requests.exceptions.RequestException("timeout"),
            type("Resp", (), {"status_code": 200, "content": b"{}", "json": lambda: {}})(),
        ]

        data = cj_adapter._make_request("GET", "/ping")
        assert isinstance(data, dict)
        assert mock_session.request.call_count == 3
