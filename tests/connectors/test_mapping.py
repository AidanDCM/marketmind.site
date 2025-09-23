"""Tests for the mapping/normalization utilities."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from packages.connectors.mapping.normalize import (
    _parse_datetime,
    denormalize_listing,
    normalize_customer,
    normalize_inventory,
    normalize_order,
    normalize_product,
)
from packages.database.models import ChannelListing


def test_parse_datetime():
    """Test datetime parsing from various formats."""
    # Test ISO format with timezone
    dt = _parse_datetime("2023-01-01T12:00:00+00:00")
    assert dt == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Test ISO format with Z
    dt = _parse_datetime("2023-01-01T12:00:00Z")
    assert dt == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Test date only
    dt = _parse_datetime("2023-01-01")
    assert dt.date() == datetime(2023, 1, 1).date()

    # Test invalid date
    now = datetime.now(timezone.utc)
    dt = _parse_datetime("invalid-date")
    # Should be recent if parsing fails
    assert abs((dt - now).total_seconds()) < 10


def test_normalize_amazon_product():
    """Test normalizing Amazon product data."""
    amazon_data = {
        "ItemAttributes": {
            "Title": "Test Product",
            "Description": "A test product",
            "Brand": "Test Brand",
        },
        "ASIN": "TEST123",
    }

    product = normalize_product(amazon_data, "amazon", "org-123")

    assert product.org_id == "org-123"
    assert product.title == "Test Product"
    assert product.description == "A test product"
    assert product.brand == "Test Brand"
    assert product.created_at.tzinfo == timezone.utc


def test_normalize_shopify_product():
    """Test normalizing Shopify product data."""
    shopify_data = {
        "title": "Shopify Product",
        "body_html": "<p>Shopify description</p>",
        "vendor": "Shopify Brand",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-02T12:00:00Z",
    }

    product = normalize_product(shopify_data, "shopify", "org-123")

    assert product.org_id == "org-123"
    assert product.title == "Shopify Product"
    assert "Shopify description" in product.description
    assert product.brand == "Shopify Brand"
    assert product.created_at == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert product.updated_at == datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc)


def test_normalize_amazon_order():
    """Test normalizing Amazon order data."""
    amazon_data = {
        "AmazonOrderId": "123-1234567-1234567",
        "OrderStatus": "Shipped",
        "OrderTotal": {"Amount": "29.99", "CurrencyCode": "USD"},
        "PurchaseDate": "2023-01-01T12:00:00Z",
    }

    order = normalize_order(amazon_data, "amazon", "org-123")

    assert order.org_id == "org-123"
    assert order.order_number == "123-1234567-1234567"
    assert order.status == "SHIPPED"
    assert order.total == Decimal("29.99")
    assert order.currency == "USD"
    assert order.created_at == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_normalize_shopify_order():
    """Test normalizing Shopify order data."""
    shopify_data = {
        "order_number": 1001,
        "financial_status": "paid",
        "total_price": "99.99",
        "currency": "USD",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-02T12:00:00Z",
    }

    order = normalize_order(shopify_data, "shopify", "org-123")

    assert order.org_id == "org-123"
    assert order.order_number == "1001"
    assert order.status == "PAID"
    assert order.total == Decimal("99.99")
    assert order.currency == "USD"
    assert order.created_at == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert order.updated_at == datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc)


def test_denormalize_amazon_listing():
    """Test converting a listing to Amazon format."""
    listing = ChannelListing(
        org_id="org-123",
        sku="TEST-SKU",
        price=Decimal("29.99"),
        currency="USD",
        quantity_available=10,
    )

    result = denormalize_listing(listing, "amazon")

    assert result["SellerSKU"] == "TEST-SKU"
    assert result["StandardPrice"]["Amount"] == "29.99"
    assert result["StandardPrice"]["CurrencyCode"] == "USD"
    assert result["Quantity"] == 10


def test_denormalize_shopify_listing():
    """Test converting a listing to Shopify format."""
    listing = ChannelListing(
        org_id="org-123",
        sku="TEST-SKU",
        price=Decimal("29.99"),
        currency="USD",
        quantity_available=5,
    )

    result = denormalize_listing(listing, "shopify")

    assert "variant" in result
    assert result["variant"]["price"] == "29.99"
    assert result["variant"]["inventory_quantity"] == 5


def test_unsupported_vendor():
    """Test that unsupported vendor types raise appropriate errors."""
    with pytest.raises(ValueError, match="Unsupported vendor type: unsupported"):
        normalize_product({}, "unsupported", "org-123")

    with pytest.raises(ValueError, match="Unsupported vendor type: unsupported"):
        normalize_order({}, "unsupported", "org-123")

    with pytest.raises(ValueError, match="Unsupported vendor type: unsupported"):
        normalize_customer({}, "unsupported", "org-123")

    with pytest.raises(ValueError, match="Unsupported vendor type: unsupported"):
        normalize_inventory({}, "unsupported", "org-123")

    listing = ChannelListing(org_id="org-123", sku="TEST")
    with pytest.raises(ValueError, match="Unsupported vendor type: unsupported"):
        denormalize_listing(listing, "unsupported")


def test_normalize_amazon_customer():
    """Test normalizing Amazon customer data."""
    amazon_data = {
        "BuyerInfo": {"BuyerEmail": "test@example.com", "BuyerName": "Test User"},
        "PurchaseDate": "2023-01-01T12:00:00Z",
    }

    customer = normalize_customer(amazon_data, "amazon", "org-123")

    assert customer.org_id == "org-123"
    assert customer.email == "test@example.com"
    assert customer.created_at == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_normalize_shopify_customer():
    """Test normalizing Shopify customer data."""
    shopify_data = {
        "email": "shopify@example.com",
        "first_name": "Shopify",
        "last_name": "User",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-02T12:00:00Z",
    }

    customer = normalize_customer(shopify_data, "shopify", "org-123")

    assert customer.org_id == "org-123"
    assert customer.email == "shopify@example.com"
    assert customer.first_name == "Shopify"
    assert customer.last_name == "User"
    assert customer.created_at == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert customer.updated_at == datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc)


def test_normalize_amazon_inventory():
    """Test normalizing Amazon inventory data."""
    amazon_data = {
        "SellerSKU": "TEST-SKU",
        "TotalSupplyQuantity": "15",
        "InStockSupplyQuantity": "10",
        "EarliestAvailability": {"TimepointType": "DateTime", "DateTime": "2023-01-01T12:00:00Z"},
    }

    inventory = normalize_inventory(amazon_data, "amazon", "org-123")

    assert inventory.org_id == "org-123"
    assert inventory.sku == "TEST-SKU"
    assert inventory.quantity == 15
    assert inventory.event_type == "SYNC"
    assert inventory.source == "amazon"
    assert inventory.created_at.tzinfo == timezone.utc


def test_normalize_shopify_inventory():
    """Test normalizing Shopify inventory data."""
    shopify_data = {
        "sku": "TEST-SKU",
        "inventory_quantity": 5,
        "updated_at": "2023-01-01T12:00:00Z",
    }

    inventory = normalize_inventory(shopify_data, "shopify", "org-123")

    assert inventory.org_id == "org-123"
    assert inventory.sku == "TEST-SKU"
    assert inventory.quantity == 5
    assert inventory.event_type == "SYNC"
    assert inventory.source == "shopify"
    assert inventory.created_at == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
