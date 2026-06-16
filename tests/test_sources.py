"""Slice 27: read-only live data sources (Stripe + Shopify)."""

import pytest

from marketmind.schemas import ImportRowStatus
from marketmind.sources import ShopifyReader, StripeReader

# ---------------------------------------------------------------------------
# Construction / credentials
# ---------------------------------------------------------------------------


def test_stripe_reader_requires_key():
    with pytest.raises(ValueError, match="api_key is required"):
        StripeReader("")


def test_stripe_from_env_missing_raises(monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="STRIPE_API_KEY"):
        StripeReader.from_env()


def test_shopify_from_env_missing_raises(monkeypatch):
    monkeypatch.delenv("SHOPIFY_STORE_DOMAIN", raising=False)
    monkeypatch.delenv("SHOPIFY_ACCESS_TOKEN", raising=False)
    with pytest.raises(ValueError, match="SHOPIFY_STORE_DOMAIN"):
        ShopifyReader.from_env()


# ---------------------------------------------------------------------------
# Stripe normalization (mocked _get)
# ---------------------------------------------------------------------------


def test_stripe_fetch_orders_normalizes(monkeypatch):
    def fake_get(self, path, params):
        assert path == "/charges"
        return {
            "data": [
                {
                    "id": "ch_1",
                    "amount": 5900,
                    "created": 1_700_000_000,
                    "status": "succeeded",
                    "refunded": False,
                    "metadata": {"product_name": "Interior Kit"},
                },
                {
                    "id": "ch_2",
                    "amount": 1999,
                    "created": 1_700_000_500,
                    "status": "succeeded",
                    "refunded": True,
                    "description": "Fallback Name",
                },
            ]
        }

    monkeypatch.setattr(StripeReader, "_get", fake_get)
    result = StripeReader("sk_test_x").fetch_orders()
    assert result.source == "stripe_charges"
    assert result.total_rows == 2
    rows = [r.data for r in result.ok_rows]
    assert rows[0]["order_id"] == "ch_1"
    assert rows[0]["product_name"] == "Interior Kit"
    assert rows[0]["sale_price"] == "59.00"
    assert rows[0]["refunded"] == "false"
    assert rows[0]["date"].startswith("20")  # ISO timestamp
    # Falls back to description when metadata has no product_name.
    assert rows[1]["product_name"] == "Fallback Name"
    assert rows[1]["sale_price"] == "19.99"
    assert rows[1]["refunded"] == "true"
    assert result.ok_rows[0].status == ImportRowStatus.OK


def test_stripe_key_not_in_output(monkeypatch):
    def fake_get(self, path, params):
        return {"data": [{"id": "ch_1", "amount": 100, "created": 1, "status": "ok"}]}

    monkeypatch.setattr(StripeReader, "_get", fake_get)
    result = StripeReader("sk_live_SECRET").fetch_orders()
    assert "sk_live_SECRET" not in str(result.to_dict())


# ---------------------------------------------------------------------------
# Shopify normalization (mocked _get)
# ---------------------------------------------------------------------------


def test_shopify_fetch_orders_normalizes(monkeypatch):
    def fake_get(self, path, params):
        assert path == "/orders.json"
        return {
            "orders": [
                {
                    "id": 111,
                    "created_at": "2026-06-16T10:00:00Z",
                    "total_price": "59.00",
                    "financial_status": "paid",
                    "fulfillment_status": "fulfilled",
                    "line_items": [{"title": "Interior Kit"}],
                    "shipping_lines": [{"price": "4.50"}],
                },
                {
                    "id": 112,
                    "created_at": "2026-06-16T11:00:00Z",
                    "total_price": "19.99",
                    "financial_status": "refunded",
                    "fulfillment_status": None,
                    "line_items": [],
                    "shipping_lines": [],
                },
            ]
        }

    monkeypatch.setattr(ShopifyReader, "_get", fake_get)
    result = ShopifyReader("shop.myshopify.com", "tok").fetch_orders()
    assert result.source == "shopify_orders"
    rows = [r.data for r in result.ok_rows]
    assert rows[0]["order_id"] == "111"
    assert rows[0]["product_name"] == "Interior Kit"
    assert rows[0]["shipping_cost"] == "4.50"
    assert rows[0]["refunded"] == "false"
    assert rows[1]["refunded"] == "true"
    assert rows[1]["product_name"] == ""  # no line items
    assert rows[1]["shipping_cost"] == ""


def test_shopify_fetch_products_normalizes(monkeypatch):
    def fake_get(self, path, params):
        assert path == "/products.json"
        return {
            "products": [
                {
                    "title": "Interior Kit",
                    "product_type": "Auto",
                    "status": "active",
                    "variants": [{"price": "59.00"}],
                }
            ]
        }

    monkeypatch.setattr(ShopifyReader, "_get", fake_get)
    result = ShopifyReader("shop.myshopify.com", "tok").fetch_products()
    assert result.source == "shopify_products"
    row = result.ok_rows[0].data
    assert row["product_name"] == "Interior Kit"
    assert row["sale_price"] == "59.00"
    assert row["niche"] == "Auto"
