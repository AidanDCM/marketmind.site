"""
Tests for the data normalization functions.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.scoping import scoped_session

from packages.connectors.mapping.normalize import (
    denormalize_listing,
    normalize_customer,
    normalize_order,
    normalize_product,
)

# Test data for Amazon product
AMAZON_PRODUCT = {
    "ItemAttributes": {
        "Title": "Test Product",
        "Description": "A test product",
        "Brand": "Test Brand",
        "SKU": "TEST-SKU-123",
    },
    "ASIN": "B07K3S79ZS",
}

# Test data for Shopify product
SHOPIFY_PRODUCT = {
    "title": "Shopify Test Product",
    "body_html": "A test product from Shopify",
    "vendor": "Shopify Test Brand",
    "variants": [{"sku": "SHOPIFY-SKU-123"}],
}

# Test data for Amazon order
AMAZON_ORDER = {
    "AmazonOrderId": "123-1234567-1234567",
    "OrderStatus": "Shipped",
    "OrderTotal": {"Amount": "29.99", "CurrencyCode": "USD"},
    "PurchaseDate": "2023-01-01T12:00:00Z",
    "ShippingAddress": {
        "Name": "John Doe",
        "AddressLine1": "123 Test St",
        "City": "Seattle",
        "StateOrRegion": "WA",
        "PostalCode": "98101",
        "CountryCode": "US",
        "Phone": "123-456-7890",
    },
}

# Test data for Shopify order
SHOPIFY_ORDER = {
    "order_number": 1001,
    "financial_status": "paid",
    "total_price": "59.99",
    "currency": "USD",
    "created_at": "2023-01-01T12:00:00Z",
    "shipping_address": {
        "first_name": "Jane",
        "last_name": "Smith",
        "address1": "456 Test Ave",
        "city": "Portland",
        "province": "OR",
        "zip": "97201",
        "country": "US",
        "phone": "987-654-3210",
    },
}


def test_normalize_product_amazon(db_session: scoped_session):
    """Test normalizing an Amazon product."""

    # Set up test data
    db_session.begin_nested()

    try:
        product = normalize_product(AMAZON_PRODUCT, "amazon", "test-org-123")

        assert product is not None
        assert isinstance(product, dict)  # Should return a dict, not a model instance
        assert product.get("title") == "Test Product"
        assert product.get("description") == "A test product"
        assert product.get("brand") == "Test Brand"
        assert product.get("sku") == "TEST-SKU-123"
        assert product.get("external_id") == "B07K3S79ZS"
    finally:
        db_session.rollback()


def test_normalize_product_shopify(db_session: scoped_session):
    """Test normalizing a Shopify product."""
    # Set up test data
    db_session.begin_nested()

    try:
        product = normalize_product(SHOPIFY_PRODUCT, "shopify", "test-org-123")

        assert product is not None
        assert isinstance(product, dict)  # Should return a dict, not a model instance
        assert product.get("title") == "Shopify Test Product"
        assert product.get("description") == "A test product from Shopify"
        assert product.get("brand") == "Shopify Test Brand"
        assert product.get("sku") == "SHOPIFY-SKU-123"
    finally:
        db_session.rollback()


def test_normalize_order_amazon(db_session: scoped_session):
    """Test normalizing an Amazon order."""
    # Set up test data
    db_session.begin_nested()

    try:
        order = normalize_order(AMAZON_ORDER, "amazon", "test-org-123")

        assert order is not None
        assert isinstance(order, dict)  # Should return a dict, not a model instance
        assert order.get("order_id") == "123-1234567-1234567"
        assert order.get("status") == "Shipped"
        assert order.get("total_amount") == Decimal("29.99")
        assert order.get("currency") == "USD"
        # Compare timestamps without timezone for simplicity
        assert order.get("order_date").replace(tzinfo=None) == datetime(2023, 1, 1, 12, 0, 0)
    finally:
        db_session.rollback()


def test_normalize_order_shopify(db_session: scoped_session):
    """Test normalizing a Shopify order."""
    # Set up test data
    db_session.begin_nested()

    try:
        order = normalize_order(SHOPIFY_ORDER, "shopify", "test-org-123")

        assert order is not None
        assert isinstance(order, dict)  # Should return a dict, not a model instance
        # Expectations are derived from SHOPIFY_ORDER fixture above
        assert order.get("order_id") == "1001"
        assert order.get("status") == "paid"
        assert order.get("total_amount") == Decimal("59.99")
        assert order.get("currency") == "USD"
        # Compare timestamps without timezone for simplicity
        assert order.get("order_date").replace(tzinfo=None) == datetime(2023, 1, 1, 12, 0, 0)
    finally:
        db_session.rollback()


def test_denormalize_listing(db_session: scoped_session):
    """Test denormalizing a listing to vendor format."""
    # Set up test data
    db_session.begin_nested()

    try:
        # Create a test product as a dictionary
        product = {
            "org_id": "test-org-123",
            "title": "Test Product",
            "description": "A test product",
            "brand": "Test Brand",
            "sku": "TEST-SKU-123",
            "external_id": "B07K3S79ZS",
            "price": Decimal("29.99"),
            "currency": "USD",
            "quantity": 10,
            "status": "active",
            "created_at": datetime(2023, 1, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2023, 1, 1, tzinfo=timezone.utc),
        }

        # Test Amazon format
        amazon_listing = denormalize_listing(product, "amazon")
        assert amazon_listing["ItemAttributes"]["Title"] == "Test Product"
        assert amazon_listing["ItemAttributes"]["Description"] == "A test product"
        assert amazon_listing["ItemAttributes"]["Brand"] == "Test Brand"
        assert amazon_listing["ItemAttributes"]["SKU"] == "TEST-SKU-123"
        assert amazon_listing["ASIN"] == "B07K3S79ZS"

        # Test Shopify format
        shopify_listing = denormalize_listing(product, "shopify")
        assert shopify_listing["title"] == "Test Product"
        assert shopify_listing["body_html"] == "A test product"
        assert shopify_listing["vendor"] == "Test Brand"
        assert shopify_listing["variants"][0]["sku"] == "TEST-SKU-123"
    finally:
        db_session.rollback()


def test_normalize_customer(db_session: scoped_session):
    """Test normalizing customer data."""
    # Set up test data
    db_session.begin_nested()

    try:
        customer_data = {
            "id": "12345",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "123-456-7890",
            "addresses": [
                {
                    "id": "1",
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Test St",
                    "city": "Seattle",
                    "province": "WA",
                    "zip": "98101",
                    "country": "US",
                    "phone": "123-456-7890",
                    "default": True,
                }
            ],
        }

        customer = normalize_customer(customer_data, "shopify", "test-org-123")

        assert customer is not None
        assert isinstance(customer, dict)  # Should return a dict, not a model instance
        assert customer.get("org_id") == "test-org-123"
        assert customer.get("first_name") == "John"
        assert customer.get("last_name") == "Doe"
        assert customer.get("email") == "john.doe@example.com"
        assert customer.get("phone") == "123-456-7890"
        assert len(customer.get("addresses", [])) == 1
        assert customer.get("addresses", [{}])[0].get("address_line1") == "123 Test St"
    finally:
        db_session.rollback()
    assert customer.city == "Seattle"
    assert customer.state == "WA"
    assert customer.postal_code == "98101"
    assert customer.country == "US"
