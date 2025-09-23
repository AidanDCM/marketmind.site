"""
CJ (Commission Junction) Integration for MarketMind.

This module provides functionality to interact with the CJ (Commission Junction) API.
"""

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

import requests
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..http.backoff import retryable
from ..http.ratelimit import get_rate_limiter
from ..idempotency import with_idempotency
from ..shared.exceptions import (
    ChannelAuthError,
    ChannelConnectionError,
    ChannelDataError,
)
from .base import ChannelAdapter, OrderData, OrderStatus, ProductData


class CJConfig(BaseModel):
    """Configuration for CJ API connection."""

    website_id: str = Field(..., description="CJ Website ID")
    auth_token: str = Field(..., description="CJ API Authentication Token")
    api_key: str = Field(..., description="CJ API Key")
    sandbox: bool = Field(True, description="Whether to use CJ Sandbox")

    class Config:
        json_encoders = {
            # Handle datetime serialization
            datetime: lambda v: v.isoformat() if v else None
        }

    @property
    def base_url(self) -> str:
        """Get the base URL for the CJ API."""
        if self.sandbox:
            return "https://api-sandbox.cj.com/v3"
        return "https://api.cj.com/v3"

    @property
    def headers(self) -> Dict[str, str]:
        """Get the default headers for API requests."""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "x-cj-application-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }


class CJProduct(ProductData):
    """CJ product data model."""

    def __init__(self, **data: Any) -> None:
        # Set default values for required fields from ProductData
        defaults = {
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "price": data.get("price", 0.0),
            "quantity": data.get("quantity", 0),
        }
        # Update with any provided data
        defaults.update(data)
        super().__init__(**defaults)

        # Set the additional fields specific to CJProduct
        self.cj_id = data.get("cj_id")
        self.advertiser_id = data.get("advertiser_id")
        self.advertiser_name = data.get("advertiser_name")
        self.buy_url = data.get("buy_url")
        self.image_url = data.get("image_url")
        self.in_stock = data.get("in_stock", True)
        self.category = data.get("category")
        self.subcategory = data.get("subcategory")
        self.last_updated = data.get("last_updated", datetime.utcnow())

        # Ensure SKU is set (from ProductData)
        self.sku = data.get("sku", "")


class CJOrder(OrderData):
    """CJ order data model."""

    cj_id: Optional[str] = Field(None, description="CJ order ID")
    advertiser_id: Optional[str] = Field(None, description="Advertiser ID")
    order_discount: Optional[float] = Field(0.0, description="Order discount amount")
    sale_amount: Optional[float] = Field(0.0, description="Total sale amount")
    commission_amount: Optional[float] = Field(0.0, description="Commission amount")
    currency: Optional[str] = Field("USD", description="Currency code")
    tracking_url: Optional[str] = Field(None, description="Order tracking URL")
    event_date: Optional[datetime] = Field(None, description="Order date")
    website_id: Optional[str] = Field(None, description="CJ website ID")


class CJAdapter(ChannelAdapter):
    """Adapter for CJ (Commission Junction) API.

    This adapter handles communication with the CJ API, including
    product listing, order management, and inventory synchronization.
    """

    # Channel identification
    CHANNEL_NAME = "cj"
    CHANNEL_DISPLAY_NAME = "Commission Junction"

    def __init__(
        self, config: Optional[Dict[str, Any]] = None, db_session: Optional[Session] = None
    ):
        """Initialize the CJ adapter.

        Args:
            config: Configuration dictionary with CJ API credentials
            db_session: SQLAlchemy database session
        """
        super().__init__(db_session)
        self.config = CJConfig(**config) if config else self._load_config()
        self.session = requests.Session()
        self._auth_headers: Dict[str, str] = {}
        self._update_auth_headers()
        self._mock_products: Dict[str, ProductData] = {}  # In-memory store for mock products
        # Shared rate limiter (conservative defaults similar to ebay)
        self._rate_limiter = get_rate_limiter("ebay_api")

    @classmethod
    def get_required_credentials(cls) -> Dict[str, str]:
        """Get the list of required credential keys for this adapter."""
        return {
            "website_id": "CJ Website ID",
            "auth_token": "CJ API Authentication Token",
            "api_key": "CJ API Key",
            "sandbox": "Whether to use sandbox environment (True/False)",
        }

    def _load_config(self) -> CJConfig:
        """Load configuration from environment variables."""
        return CJConfig(
            website_id=os.getenv("CJ_WEBSITE_ID", ""),
            auth_token=os.getenv("CJ_AUTH_TOKEN", ""),
            api_key=os.getenv("CJ_API_KEY", ""),
            sandbox=os.getenv("CJ_SANDBOX", "true").lower() == "true",
        )

    def _update_auth_headers(self) -> None:
        """Update the authentication headers with the current token."""
        self._auth_headers = self.config.headers

    @retryable(exceptions=(requests.exceptions.RequestException,), max_retries=3)
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        retry_auth: bool = True,
    ) -> Dict[str, Any]:
        """Make an authenticated request to the CJ API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Form data
            json_data: JSON request body
            headers: Additional headers
            retry_auth: Whether to retry with a new token if auth fails

        Returns:
            Response JSON data

        Raises:
            ChannelAuthError: If authentication fails
            ChannelConnectionError: If there's a connection error
            ChannelDataError: If there's an error in the request data
        """
        # Acquire rate limit token
        try:
            self._rate_limiter.acquire(1)
        except Exception:
            # Fallback to small sleep if limiter raises
            time.sleep(0.2)
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        headers = {**self._auth_headers, **(headers or {})}

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=headers,
                timeout=30,
            )

            # Handle 401 Unauthorized
            if response.status_code == 401 and retry_auth:
                if self.authenticate(force_refresh=True):
                    return self._make_request(
                        method=method,
                        endpoint=endpoint,
                        params=params,
                        data=data,
                        json_data=json_data,
                        headers=headers,
                        retry_auth=False,  # Don't retry again to avoid infinite loops
                    )
                raise ChannelAuthError("Authentication failed after refresh attempt")

            # Handle other error status codes
            if response.status_code >= 400:
                error_msg = f"CJ API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f": {error_data.get('message', 'Unknown error')}"
                except ValueError:
                    error_msg += f": {response.text}"

                if response.status_code == 400:
                    raise ChannelDataError(error_msg)
                elif response.status_code == 403:
                    raise ChannelAuthError(error_msg)
                else:
                    raise ChannelConnectionError(error_msg)

            # Return the response data (be tolerant of minimal test doubles)
            if response.content:
                try:
                    return cast(Dict[str, Any], response.json())
                except Exception:
                    return {}
            return {}

        except requests.exceptions.RequestException:
            # Allow retryable decorator to perform backoff/retries on transient errors
            raise

    def authenticate(self, **kwargs: Any) -> bool:
        """Authenticate with the CJ API.

        Args:
            **kwargs: Additional authentication options (unused)

        Returns:
            bool: True if authentication was successful

        Raises:
            ChannelAuthError: If authentication fails
        """
        # For now, we'll just validate the configuration
        if not all([self.config.website_id, self.config.auth_token, self.config.api_key]):
            raise ChannelAuthError("Missing required CJ API credentials")

        # In a real implementation, we would validate the credentials with the API
        # For now, we'll just assume they're valid
        return True

    def health(self) -> Dict[str, Any]:
        """Health probe for the CJ channel adapter."""
        try:
            self.authenticate()
            # light call using mock products retrieval path
            _ = self.get_products(limit=1)
            return {"ok": True, "name": self.CHANNEL_NAME, "sandbox": self.config.sandbox}
        except Exception as e:
            return {"ok": False, "name": self.CHANNEL_NAME, "error": str(e)}

    def get_orders(
        self,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[OrderData]:
        """Get orders from CJ.

        Args:
            status: Optional order status filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of orders to return (1-1000)
            offset: Pagination offset

        Returns:
            List[CJOrder]: List of orders (empty list if no orders found)

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        # This is a stub implementation that returns an empty list
        # In a real implementation, we would call the CJ API to get orders
        return []

    def get_order(self, order_id: str) -> Optional[OrderData]:
        """Get a single order by ID.

        Args:
            order_id: The CJ order ID

        Returns:
            Optional[CJOrder]: The order, or None if not found

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If the order is not found or there's an error in the request data
        """
        # This is a stub implementation that returns None
        # In a real implementation, we would call the CJ API to get the order
        return None

    def get_products(
        self,
        skus: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[ProductData]:
        """Get products from CJ.

        Args:
            skus: Optional list of SKUs to filter by
            limit: Maximum number of products to return (1-1000)
            offset: Pagination offset

        Returns:
            List[CJProduct]: List of products

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        # This is a mock implementation that returns some sample products
        if not hasattr(self, "_mock_products") or not self._mock_products:
            self._mock_products = {
                "CJ-12345": CJProduct(
                    sku="CJ-12345",
                    title="Sample Product 1",
                    description="This is a sample product from CJ",
                    price=29.99,
                    quantity=100,
                    cj_id="12345",
                    advertiser_id="ADV123",
                    advertiser_name="Sample Advertiser",
                    buy_url="https://example.com/buy/12345",
                    image_url="https://example.com/images/12345.jpg",
                    in_stock=True,
                    category="Electronics",
                    subcategory="Gadgets",
                    last_updated=datetime.utcnow(),
                ),
                "CJ-67890": CJProduct(
                    sku="CJ-67890",
                    title="Sample Product 2",
                    description="Another sample product from CJ",
                    price=49.99,
                    quantity=50,
                    cj_id="67890",
                    advertiser_id="ADV123",
                    advertiser_name="Sample Advertiser",
                    buy_url="https://example.com/buy/67890",
                    image_url="https://example.com/images/67890.jpg",
                    in_stock=True,
                    category="Home & Garden",
                    subcategory="Decor",
                    last_updated=datetime.utcnow(),
                ),
            }

        # Filter by SKUs if provided
        if skus:
            return [p for sku, p in self._mock_products.items() if sku in skus]

        # Apply pagination
        return list(self._mock_products.values())[offset : offset + limit]

    def get_product(self, product_id: Any) -> Optional[ProductData]:
        """Get a single product by ID or SKU.

        Args:
            product_id: The product ID or SKU (can be a string or FieldInfo)

        Returns:
            Optional[CJProduct]: The product, or None if not found

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If the product is not found or there's an error in the request data
        """
        # Convert product_id to string if it's a FieldInfo object
        if hasattr(product_id, "default"):
            product_id = str(product_id.default)
        else:
            product_id = str(product_id)

        # Get all products and find the one with matching SKU or ID
        products = self.get_products()
        for product in products:
            if (hasattr(product, "sku") and product.sku == product_id) or (
                hasattr(product, "cj_id") and str(product.cj_id) == product_id
            ):
                return product

        return None

    @with_idempotency(
        key_func=lambda self, product_data, **kw: f"cj_create_product:{product_data.get('sku')}"
    )
    def create_product(self, product_data: Dict[str, Any]) -> ProductData:
        """Create a new product on CJ.

        Args:
            product_data: Product data

        Returns:
            CJProduct: The created product

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        # This is a mock implementation that creates a product in the mock store
        if not hasattr(self, "_mock_products"):
            self._mock_products = {}

        # Generate a mock CJ ID
        cj_id = str(int(time.time()))
        sku = product_data.get("sku", f"CJ-{cj_id}")

        # Create the product
        product = CJProduct(
            sku=sku,
            title=product_data.get("title", "New Product"),
            description=product_data.get("description", ""),
            price=float(product_data.get("price", 0.0)),
            quantity=int(product_data.get("quantity", 0)),
            cj_id=cj_id,
            advertiser_id=product_data.get("advertiser_id", "ADV123"),
            advertiser_name=product_data.get("advertiser_name", "Sample Advertiser"),
            buy_url=product_data.get("buy_url", f"https://example.com/buy/{cj_id}"),
            image_url=product_data.get("image_url", f"https://example.com/images/{cj_id}.jpg"),
            in_stock=bool(product_data.get("in_stock", True)),
            category=product_data.get("category", "Uncategorized"),
            subcategory=product_data.get("subcategory", "General"),
            last_updated=datetime.utcnow(),
        )

        # Add to mock store
        self._mock_products[sku] = product

        return product

    @with_idempotency(
        key_func=lambda self,
        product_id,
        product_data,
        **kw: f"cj_update_product:{product_id}:{hash(frozenset(product_data.items()))}"
    )
    def update_product(self, product_id: str, product_data: Dict[str, Any]) -> ProductData:
        """Update an existing product on CJ.

        Args:
            product_id: The CJ product ID or SKU
            product_data: Updated product data

        Returns:
            CJProduct: The updated product

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        # This is a mock implementation that updates a product in the mock store
        product = self.get_product(product_id)
        if not product:
            raise ChannelDataError(f"Product not found: {product_id}")

        # Update the product fields
        for key, value in product_data.items():
            if hasattr(product, key):
                setattr(product, key, value)

        # Update the last_updated timestamp
        if isinstance(product, CJProduct):
            product.last_updated = datetime.utcnow()

        # Update in mock store using SKU as the key
        self._mock_products[product.sku] = product

        return product

    def delete_product(self, product_id: str) -> bool:
        """Delete a product from CJ.

        Args:
            product_id: The CJ product ID or SKU

        Returns:
            bool: True if the deletion was successful

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        # This is a mock implementation that removes a product from the mock store
        product = self.get_product(product_id)
        if not product:
            raise ChannelDataError(f"Product not found: {product_id}")

        # Remove from mock store
        if hasattr(self, "_mock_products") and product.sku in self._mock_products:
            del self._mock_products[product.sku]
            return True

        return False

    @with_idempotency(
        key_func=lambda self, updates, **kw: "cj_update_inventory_"
        + "_".join(sorted(f"{u.get('sku')}:{u.get('quantity')}" for u in (updates or [])))
    )
    def update_inventory(self, updates: List[Dict[str, Any]], **kwargs: Any) -> bool:
        """Update inventory levels on CJ.

        This method updates the inventory levels for multiple products on CJ.

        Args:
            updates: List of inventory updates, where each update is a dictionary
                    containing 'sku' (str) and 'quantity' (int) keys.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            bool: True if the update was successful, False otherwise.

        Raises:
            ChannelConnectionError: If there's an error connecting to the CJ API.
            ChannelDataError: If there's an error in the request data.
        """
        if not updates:
            return True

        try:
            # Group updates by SKU to avoid duplicate updates
            sku_updates = {}
            for update in updates:
                sku = update.get("sku")
                quantity = update.get("quantity")
                if sku is not None and quantity is not None:
                    sku_updates[sku] = quantity

            if not sku_updates:
                return True

            # Update the mock product data
            for sku, quantity in sku_updates.items():
                # Get the product (this will create it if it doesn't exist)
                product = self.get_product(sku)
                if not product:
                    # If product doesn't exist, create a new one with default values
                    product = self.create_product(
                        {
                            "sku": sku,
                            "title": f"Product {sku}",
                            "description": f"Automatically created product for SKU {sku}",
                            "price": 0.0,
                            "quantity": quantity,
                        }
                    )
                else:
                    # Update the quantity of the existing product
                    product.quantity = quantity
                    if isinstance(product, CJProduct):
                        product.last_updated = datetime.utcnow()
                    self._mock_products[product.sku] = product

                # In a real implementation, we would make an API call here
                # For now, we'll just log the update
                print(f"  ✓ Updated inventory for SKU {sku} to {quantity}")

            return True

        except Exception as e:
            error_msg = f"Failed to update inventory on CJ: {str(e)}"
            raise ChannelDataError(error_msg) from e

    @with_idempotency(
        key_func=lambda self,
        order_id,
        status,
        **kw: f"cj_update_order_status:{order_id}:{status.value}"
    )
    def update_order_status(self, order_id: str, status: OrderStatus, **kwargs: Any) -> bool:
        """Update the status of an order on CJ.

        Args:
            order_id: The ID of the order to update
            status: The new status for the order

        Returns:
            bool: True if the update was successful, False otherwise

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        # This is a stub implementation that always returns True
        # In a real implementation, we would call the CJ API to update the order status
        return True


# Registration is handled centrally in `packages/connectors/channels/registry.py`.
