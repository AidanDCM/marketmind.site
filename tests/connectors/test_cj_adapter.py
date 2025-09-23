"""
Tests for the CJ (Commission Junction) channel adapter.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from packages.connectors.channels.base import OrderStatus
from packages.connectors.channels.cj import CJAdapter, CJProduct

# Test configuration
TEST_CONFIG = {
    "website_id": "12345678",
    "auth_token": "test_auth_token_123",
    "api_key": "test_api_key_456",
    "sandbox": True,
}

# Sample test data
SAMPLE_ORDER = {
    "orderId": "1234567890",
    "orderStatus": "completed",
    "orderTotal": "29.99",
    "currency": "USD",
    "orderDate": "2023-01-01T12:00:00.000Z",
    "items": [
        {"sku": "CJ-12345", "quantity": 1, "saleAmount": "29.99", "commissionAmount": "2.99"}
    ],
    "customer": {"email": "test@example.com"},
    "advertiserId": "ADV123",
    "websiteId": "12345678",
}

SAMPLE_PRODUCT = {
    "sku": "CJ-12345",
    "name": "Test Product",
    "description": "This is a test product",
    "price": "29.99",
    "salePrice": "24.99",
    "inStock": True,
    "category": "Electronics",
    "subcategory": "Gadgets",
    "url": "https://example.com/product/cj-12345",
    "imageUrl": "https://example.com/images/cj-12345.jpg",
    "advertiserId": "ADV123",
    "advertiserName": "Test Advertiser",
    "lastUpdated": "2023-01-01T12:00:00.000Z",
}


class MockProduct:
    def __init__(self, sku, title, quantity=10):
        self.sku = sku
        self.title = title
        self.quantity = quantity
        self.cj_id = f"CJ-{sku}"
        self.advertiser_id = "ADV123"
        self.advertiser_name = "Test Advertiser"
        self.buy_url = f"https://example.com/buy/{sku}"
        self.image_url = f"https://example.com/images/{sku}.jpg"
        self.in_stock = True
        self.category = "Electronics"
        self.subcategory = "Gadgets"
        self.last_updated = datetime.utcnow()

    def to_dict(self):
        return {
            "sku": self.sku,
            "title": self.title,
            "quantity": self.quantity,
            "cj_id": self.cj_id,
            "advertiser_id": self.advertiser_id,
            "advertiser_name": self.advertiser_name,
            "buy_url": self.buy_url,
            "image_url": self.image_url,
            "in_stock": self.in_stock,
            "category": self.category,
            "subcategory": self.subcategory,
            "last_updated": self.last_updated,
        }


@pytest.fixture
def mock_requests():
    """Mock requests for all tests."""
    with patch("requests.Session") as mock_session:
        yield mock_session.return_value


@pytest.fixture
def mock_product():
    """Create a mock product for testing."""
    return MockProduct("12345", "Test Product")


@pytest.fixture
def cj_adapter(mock_product):
    """Create a CJAdapter instance with a mock session."""
    # Create a mock session
    with patch("requests.Session") as mock_session:
        adapter = CJAdapter(config=TEST_CONFIG)

        # Set up mock products for testing
        adapter._mock_products = {
            "CJ-12345": CJProduct(
                sku="CJ-12345",
                title="Test Product",
                description="This is a test product",
                price=29.99,
                quantity=10,
                cj_id="12345",
                advertiser_id="ADV123",
                advertiser_name="Test Advertiser",
                buy_url="https://example.com/buy/12345",
                image_url="https://example.com/images/12345.jpg",
                in_stock=True,
                category="Electronics",
                subcategory="Gadgets",
                last_updated=datetime.utcnow(),
            )
        }

        yield adapter


def test_initialization(cj_adapter):
    """Test that the adapter initializes correctly."""
    assert cj_adapter.config.website_id == TEST_CONFIG["website_id"]
    assert cj_adapter.config.auth_token == TEST_CONFIG["auth_token"]
    assert cj_adapter.config.api_key == TEST_CONFIG["api_key"]
    assert cj_adapter.config.sandbox == TEST_CONFIG["sandbox"]


def test_get_required_credentials():
    """Test that the required credentials are correct."""
    required = CJAdapter.get_required_credentials()
    assert "website_id" in required
    assert "auth_token" in required
    assert "api_key" in required
    assert "sandbox" in required


def test_authenticate_success(cj_adapter):
    """Test successful authentication."""
    # The mock implementation always returns True for authentication
    assert cj_adapter.authenticate() is True


def test_authenticate_missing_credentials():
    """Test authentication fails with missing credentials."""
    with pytest.raises(Exception):
        adapter = CJAdapter(config={"website_id": "", "auth_token": "", "api_key": ""})
        adapter.authenticate()


def test_get_products_success(cj_adapter):
    """Test successful product retrieval."""
    products = cj_adapter.get_products()

    # Should return a list of products
    assert isinstance(products, list)
    assert len(products) > 0

    # Check the first product's structure
    product = products[0]
    assert hasattr(product, "sku")
    assert hasattr(product, "title")
    assert hasattr(product, "price")
    assert hasattr(product, "quantity")
    assert hasattr(product, "cj_id")
    assert hasattr(product, "advertiser_id")
    assert hasattr(product, "advertiser_name")
    assert hasattr(product, "buy_url")
    assert hasattr(product, "image_url")
    assert hasattr(product, "in_stock")
    assert hasattr(product, "category")
    assert hasattr(product, "subcategory")
    assert hasattr(product, "last_updated")


def test_get_product_success(cj_adapter):
    """Test successful single product retrieval by SKU."""
    # Test with existing SKU
    product = cj_adapter.get_product("CJ-12345")
    assert product is not None
    assert product.sku == "CJ-12345"
    assert product.title == "Test Product"

    # Test with non-existent SKU
    product = cj_adapter.get_product("NON-EXISTENT-SKU")
    assert product is None


def test_create_product_success(cj_adapter):
    """Test successful product creation."""
    new_product_data = {
        "sku": "CJ-67890",
        "title": "New Test Product",
        "description": "A new test product",
        "price": 39.99,
        "quantity": 5,
        "advertiser_id": "ADV456",
        "advertiser_name": "Another Advertiser",
    }

    product = cj_adapter.create_product(new_product_data)

    # Verify the returned product
    assert product.sku == "CJ-67890"
    assert product.title == "New Test Product"
    assert product.price == 39.99
    assert product.quantity == 5
    assert product.advertiser_id == "ADV456"
    assert product.advertiser_name == "Another Advertiser"

    # Verify the product was added to the mock store
    assert "CJ-67890" in cj_adapter._mock_products
    assert cj_adapter._mock_products["CJ-67890"].title == "New Test Product"


def test_update_product_success(cj_adapter):
    """Test successful product update."""
    # Update an existing product
    update_data = {"title": "Updated Test Product", "price": 34.99, "quantity": 15}

    updated_product = cj_adapter.update_product("CJ-12345", update_data)

    # Verify the returned product
    assert updated_product.title == "Updated Test Product"
    assert updated_product.price == 34.99
    assert updated_product.quantity == 15

    # Verify the product was updated in the mock store
    assert cj_adapter._mock_products["CJ-12345"].title == "Updated Test Product"
    assert cj_adapter._mock_products["CJ-12345"].price == 34.99
    assert cj_adapter._mock_products["CJ-12345"].quantity == 15


def test_delete_product_success(cj_adapter):
    """Test successful product deletion."""
    # First, create a product to delete
    product_data = {
        "sku": "CJ-TO-DELETE",
        "title": "Product to Delete",
        "price": 9.99,
        "quantity": 1,
    }
    cj_adapter.create_product(product_data)

    # Verify the product exists
    assert "CJ-TO-DELETE" in cj_adapter._mock_products

    # Delete the product
    result = cj_adapter.delete_product("CJ-TO-DELETE")
    assert result is True

    # Verify the product was deleted
    assert "CJ-TO-DELETE" not in cj_adapter._mock_products


def test_update_inventory_success(cj_adapter):
    """Test successful inventory update."""
    # Update inventory for existing product
    updates = [
        {"sku": "CJ-12345", "quantity": 5},
        {"sku": "CJ-NEW-ITEM", "quantity": 10},  # This should create a new product
    ]

    result = cj_adapter.update_inventory(updates)

    # Verify the result
    assert result is True

    # Verify the existing product was updated
    assert cj_adapter._mock_products["CJ-12345"].quantity == 5

    # Verify the new product was created
    assert "CJ-NEW-ITEM" in cj_adapter._mock_products
    assert cj_adapter._mock_products["CJ-NEW-ITEM"].quantity == 10
    assert cj_adapter._mock_products["CJ-NEW-ITEM"].title == "Product CJ-NEW-ITEM"  # Default title


def test_get_orders_success(cj_adapter):
    """Test order retrieval (stub implementation)."""
    # The current implementation returns an empty list
    orders = cj_adapter.get_orders()
    assert isinstance(orders, list)
    assert len(orders) == 0


def test_update_order_status_success(cj_adapter):
    """Test order status update (stub implementation)."""
    # The current implementation always returns True
    result = cj_adapter.update_order_status("ORDER123", OrderStatus.COMPLETED)
    assert result is True
