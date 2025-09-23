"""Tests for the Amazon SP-API channel adapter."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from packages.connectors.channels.amazon import AmazonAdapter
from packages.connectors.channels.base import OrderStatus


@pytest.fixture
def mock_spapi_client():
    """Create a mock SpapiClient for testing."""
    with patch("packages.shared.spapi_client.SpapiClient") as mock:
        yield mock


@pytest.fixture
def amazon_adapter(mock_spapi_client):
    """Create an AmazonAdapter instance with a mock SpapiClient."""
    adapter = AmazonAdapter(
        client_id="test-client-id",
        client_secret="test-client-secret",
        refresh_token="test-refresh-token",
        marketplace_id="ATVPDKIKX0DER",
    )
    # Mock the client instance created in __init__
    adapter.client = mock_spapi_client.return_value
    return adapter


def test_authenticate_success(amazon_adapter, mock_spapi_client):
    """Test successful authentication."""
    # Setup mock to not raise exceptions
    result = amazon_adapter.authenticate()
    assert result is True
    amazon_adapter.client._ensure_token.assert_called_once()


def test_authenticate_failure(amazon_adapter, mock_spapi_client):
    """Test authentication failure."""
    amazon_adapter.client._ensure_token.side_effect = Exception("Auth failed")
    result = amazon_adapter.authenticate()
    assert result is False


@patch("requests.get")
def test_get_orders(mock_get, amazon_adapter):
    """Test retrieving orders."""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "payload": {
            "Orders": [
                {
                    "AmazonOrderId": "123-1234567-1234567",
                    "OrderStatus": "Shipped",
                    "PurchaseDate": "2023-01-01T12:00:00Z",
                    "LastUpdateDate": "2023-01-02T12:00:00Z",
                    "OrderTotal": {"Amount": "29.99", "CurrencyCode": "USD"},
                    "BuyerInfo": {"BuyerEmail": "test@example.com"},
                    "OrderItems": [
                        {
                            "SellerSKU": "TEST-SKU",
                            "Title": "Test Product",
                            "QuantityOrdered": 1,
                            "ItemPrice": {"Amount": "29.99", "CurrencyCode": "USD"},
                        }
                    ],
                }
            ]
        }
    }
    mock_get.return_value = mock_response

    # Call the method
    orders = amazon_adapter.get_orders()

    # Verify the results
    assert len(orders) == 1
    assert orders[0].order_id == "123-1234567-1234567"
    assert orders[0].status == OrderStatus.SHIPPED
    assert orders[0].customer_email == "test@example.com"
    assert len(orders[0].items) == 1
    assert orders[0].items[0]["sku"] == "TEST-SKU"


@patch("requests.get")
def test_get_order_success(mock_get, amazon_adapter):
    """Test retrieving a single order."""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "payload": {
            "AmazonOrderId": "123-1234567-1234567",
            "OrderStatus": "Shipped",
            "PurchaseDate": "2023-01-01T12:00:00Z",
            "LastUpdateDate": "2023-01-02T12:00:00Z",
            "OrderTotal": {"Amount": "29.99", "CurrencyCode": "USD"},
            "BuyerInfo": {"BuyerEmail": "test@example.com"},
            "OrderItems": [
                {
                    "SellerSKU": "TEST-SKU",
                    "Title": "Test Product",
                    "QuantityOrdered": 1,
                    "ItemPrice": {"Amount": "29.99", "CurrencyCode": "USD"},
                }
            ],
        }
    }
    mock_get.return_value = mock_response

    # Call the method
    order = amazon_adapter.get_order("123-1234567-1234567")

    # Verify the results
    assert order is not None
    assert order.order_id == "123-1234567-1234567"
    assert order.status == OrderStatus.SHIPPED


@patch("requests.get")
def test_get_order_not_found(mock_get, amazon_adapter):
    """Test retrieving a non-existent order."""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    # Call the method
    order = amazon_adapter.get_order("NON-EXISTENT-ORDER")

    # Verify the result
    assert order is None


@patch("requests.post")
def test_update_price_success(mock_post, amazon_adapter):
    """Test updating a product price."""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    # Call the method
    result = amazon_adapter.update_price("TEST-SKU", Decimal("19.99"))

    # Verify the result
    assert result is True
    mock_post.assert_called_once()

    # Verify the request payload
    args, kwargs = mock_post.call_args
    assert kwargs["json"] == [
        {"sku": "TEST-SKU", "price": {"currency": "USD", "amount": "19.99"}}  # Default currency
    ]


def test_normalize_order_status_mapping(amazon_adapter):
    """Test that Amazon order statuses are correctly mapped to our OrderStatus enum."""
    test_cases = [
        ("Pending", OrderStatus.PENDING),
        ("Unshipped", OrderStatus.PROCESSING),
        ("PartiallyShipped", OrderStatus.PROCESSING),
        ("Shipped", OrderStatus.SHIPPED),
        ("Canceled", OrderStatus.CANCELLED),
        ("Unfulfillable", OrderStatus.FAILED),
        ("Delivered", OrderStatus.DELIVERED),
        ("UnknownStatus", OrderStatus.PENDING),  # Default case
    ]

    for amazon_status, expected_status in test_cases:
        order_data = {
            "AmazonOrderId": "123-1234567-1234567",
            "OrderStatus": amazon_status,
            "PurchaseDate": "2023-01-01T12:00:00Z",
            "BuyerInfo": {"BuyerEmail": "test@example.com"},
            "OrderItems": [],
        }

        order = amazon_adapter._normalize_order(order_data)
        assert (
            order.status == expected_status
        ), f"Expected {amazon_status} to map to {expected_status}"


def test_competitive_pricing(amazon_adapter, mock_spapi_client):
    """Test getting competitive pricing."""
    # Setup mock return value
    expected_result = {
        "TEST-ASIN-1": {
            "status": "Success",
            "product": {
                "identifiers": {"marketplaceASIN": {"ASIN": "TEST-ASIN-1"}},
                "competitivePricing": {
                    "competitivePrices": [
                        {"condition": "New", "price": {"amount": 19.99, "currency": "USD"}}
                    ]
                },
            },
        }
    }

    # Patch the _get_competitive_pricing method to return our test data
    with patch.object(
        amazon_adapter, "_get_competitive_pricing", return_value=expected_result
    ) as mock_method:
        # Call the method
        result = amazon_adapter.get_competitive_pricing(["TEST-ASIN-1"])

        # Verify the result
        assert "TEST-ASIN-1" in result
        assert result["TEST-ASIN-1"]["status"] == "Success"

        # Verify the method was called with the correct arguments
        mock_method.assert_called_once_with(["TEST-ASIN-1"])
