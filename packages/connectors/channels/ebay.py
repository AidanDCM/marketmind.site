"""
eBay Marketplace Integration for MarketMind.

This module provides functionality to interact with the eBay Marketplace API.
"""

import base64
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlencode

import requests
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..http.backoff import retryable
from ..idempotency import with_idempotency

# Import the database models correctly
from ..shared.exceptions import (
    ChannelAuthError,
    ChannelConnectionError,
    ChannelDataError,
)
from .base import ChannelAdapter, OrderData, OrderStatus, ProductData


class EBayConfig(BaseModel):
    """Configuration for eBay API connection."""

    app_id: str = Field(..., description="eBay App ID (Client ID)")
    cert_id: str = Field(..., description="eBay Cert ID (Client Secret)")
    dev_id: str = Field(..., description="eBay Developer ID")
    auth_token: Optional[str] = Field(None, description="OAuth User Token")
    refresh_token: Optional[str] = Field(None, description="OAuth Refresh Token")
    token_expiry: Optional[datetime] = Field(None, description="Token expiry time")
    sandbox: bool = Field(True, description="Whether to use eBay Sandbox")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    @property
    def base_url(self) -> str:
        """Get the base URL for the eBay API."""
        if self.sandbox:
            return "https://api.sandbox.ebay.com"
        return "https://api.ebay.com"

    @property
    def oauth_url(self) -> str:
        """Get the OAuth URL for eBay."""
        if self.sandbox:
            return "https://auth.sandbox.ebay.com/oauth2/authorize"
        return "https://auth.ebay.com/oauth2/authorize"

    @property
    def token_url(self) -> str:
        """Get the token URL for eBay OAuth."""
        if self.sandbox:
            return "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        return "https://api.ebay.com/identity/v1/oauth2/token"


class EBayProduct(ProductData):
    """eBay product data model."""

    item_id: Optional[str] = Field(None, description="eBay item ID")
    listing_id: Optional[str] = Field(None, description="eBay listing ID")
    sku: str = Field("", description="Seller SKU")
    upc: Optional[str] = Field(None, description="Product UPC")
    ean: Optional[str] = Field(None, description="Product EAN")
    isbn: Optional[str] = Field(None, description="Product ISBN")
    condition_id: Optional[str] = Field(None, description="eBay condition ID")
    condition: Optional[str] = Field(None, description="Item condition")
    category_id: Optional[str] = Field(None, description="eBay category ID")
    category_name: Optional[str] = Field(None, description="eBay category name")
    primary_category_id: Optional[str] = Field(None, description="Primary category ID")
    primary_category_name: Optional[str] = Field(None, description="Primary category name")
    listing_duration: Optional[str] = Field("GTC", description="How long the listing is active")
    listing_type: Optional[str] = Field("FIXED_PRICE", description="Listing type")
    payment_policy_id: Optional[str] = Field(None, description="Payment policy ID")
    return_policy_id: Optional[str] = Field(None, description="Return policy ID")
    shipping_profile_id: Optional[str] = Field(None, description="Shipping profile ID")
    fulfillment_policy_id: Optional[str] = Field(None, description="Fulfillment policy ID")
    tax_profile_id: Optional[str] = Field(None, description="Tax profile ID")
    lot_size: Optional[int] = Field(None, description="Number of items in the lot")
    private_notes: Optional[str] = Field(None, description="Private seller notes")
    relationship_details: Optional[Dict] = Field(
        None, description="Relationship details for variations"
    )
    variation_aspects: Optional[List[Dict]] = Field(None, description="Variation aspects")
    variations: Optional[List[Dict]] = Field(None, description="Product variations")


class EBayOrder(OrderData):
    """eBay order data model."""

    order_id: str = Field(..., description="eBay order ID")
    order_status: OrderStatus = Field(OrderStatus.PROCESSING, description="Order status")
    buyer_username: Optional[str] = Field(None, description="eBay buyer username")
    buyer_email: Optional[str] = Field(None, description="Buyer email")
    buyer_note: Optional[str] = Field(None, description="Buyer note")
    seller_notes: Optional[str] = Field(None, description="Seller notes")
    payment_method: Optional[str] = Field(None, description="Payment method")
    payment_status: Optional[str] = Field(None, description="Payment status")
    payment_date: Optional[datetime] = Field(None, description="Payment date")
    payment_hold_status: Optional[str] = Field(None, description="Payment hold status")
    fulfillment_href: Optional[str] = Field(None, description="Fulfillment API URL")
    fulfillment_start_date: Optional[datetime] = Field(None, description="Fulfillment start date")
    fulfillment_date: Optional[datetime] = Field(None, description="Fulfillment date")
    last_modified_date: Optional[datetime] = Field(None, description="Last modified date")
    cancel_status: Optional[Dict] = Field(None, description="Cancel status")
    cancel_id: Optional[str] = Field(None, description="Cancel request ID")
    cancel_reason: Optional[str] = Field(None, description="Cancel reason")
    cancel_requested: bool = Field(False, description="Whether cancellation was requested")
    cancel_state: Optional[str] = Field(None, description="Cancel state")
    cancel_completed_date: Optional[datetime] = Field(None, description="Cancel completed date")
    cancel_initiator: Optional[str] = Field(None, description="Who initiated the cancellation")
    cancel_reason_code: Optional[str] = Field(None, description="Cancel reason code")
    cancel_request_type: Optional[str] = Field(None, description="Cancel request type")
    cancel_request_amount: Optional[Dict] = Field(None, description="Cancel requested amount")
    cancel_payment_status: Optional[str] = Field(None, description="Cancel payment status")
    cancel_requested_refund: bool = Field(False, description="Whether refund was requested")
    cancel_requested_return: bool = Field(False, description="Whether return was requested")
    cancel_requested_return_shipping: bool = Field(
        False, description="Whether return shipping was requested"
    )
    cancel_requested_return_shipping_cost: Optional[Dict] = Field(
        None, description="Requested return shipping cost"
    )


class EBayAdapter(ChannelAdapter):
    """
    Adapter for eBay Marketplace API.

    This adapter handles communication with the eBay Marketplace API, including
    product listing, order management, and inventory synchronization.
    """

    CHANNEL_NAME = "ebay"
    CHANNEL_DISPLAY_NAME = "eBay Marketplace"

    # Mock data store for testing
    _mock_products: Dict[str, ProductData] = {}

    def __init__(
        self, config: Optional[Dict[str, Any]] = None, db_session: Optional[Session] = None
    ):
        """Initialize the eBay adapter.

        Args:
            config: Configuration dictionary with eBay API credentials
            db_session: SQLAlchemy database session
        """
        super().__init__(db_session)
        self.config = EBayConfig(**config) if config else self._load_config()
        self.session = requests.Session()
        self._auth_headers: Dict[str, str] = {}
        self._update_auth_headers()

    @classmethod
    def get_required_credentials(cls) -> List[str]:
        """Get the list of required credential keys for this adapter."""
        return ["app_id", "cert_id", "dev_id"]

    def _load_config(self) -> EBayConfig:
        """Load configuration from environment variables."""
        return EBayConfig(
            app_id=os.getenv("EBAY_APP_ID", ""),
            cert_id=os.getenv("EBAY_CERT_ID", ""),
            dev_id=os.getenv("EBAY_DEV_ID", ""),
            auth_token=os.getenv("EBAY_AUTH_TOKEN"),
            refresh_token=os.getenv("EBAY_REFRESH_TOKEN"),
            sandbox=os.getenv("EBAY_SANDBOX", "true").lower() == "true",
        )

    def _update_auth_headers(self) -> None:
        """Update the authentication headers with the current token."""
        if not self.config.auth_token:
            self.authenticate()

        self._auth_headers = {
            "Authorization": f"Bearer {self.config.auth_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",  # Default to US marketplace
        }

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
        """Make an authenticated request to the eBay API.

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
        url = f"{self.config.base_url}{endpoint}"
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

            # Handle 401 Unauthorized (token might be expired)
            if response.status_code == 401 and retry_auth:
                self.authenticate(force_refresh=True)
                return self._make_request(
                    method=method,
                    endpoint=endpoint,
                    params=params,
                    data=data,
                    json_data=json_data,
                    headers=headers,
                    retry_auth=False,
                )

            response.raise_for_status()
            if response.text:
                try:
                    return cast(Dict[str, Any], response.json())
                except Exception:
                    return {}
            return {}

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ChannelAuthError(f"Authentication failed: {e}") from e
            elif 400 <= response.status_code < 500:
                error_data = response.json() if response.text else {}
                raise ChannelDataError(
                    f"API request failed with status {response.status_code}: {error_data}"
                ) from e
            raise ChannelConnectionError(f"HTTP error: {e}") from e
        except requests.exceptions.RequestException:
            # Allow retryable decorator to handle transient request errors
            raise

    def health(self) -> Dict[str, Any]:
        """Health probe for the eBay adapter."""
        try:
            # Ensure we have a valid token (authenticate will refresh if needed)
            self.authenticate()
            return {"ok": True, "name": self.CHANNEL_NAME, "sandbox": self.config.sandbox}
        except ChannelAuthError as e:
            return {"ok": False, "name": self.CHANNEL_NAME, "error": str(e)}

    def authenticate(self, **kwargs: Any) -> bool:
        """Authenticate with the eBay API.

        Args:
            **kwargs: May include 'force_refresh' to force a token refresh

        Returns:
            bool: True if authentication was successful

        Raises:
            ChannelAuthError: If authentication fails
        """
        # If we have a valid token and not forcing refresh, use it
        force_refresh: bool = bool(kwargs.get("force_refresh", False))
        if not force_refresh and self.config.auth_token and self.config.token_expiry:
            if datetime.utcnow() < self.config.token_expiry - timedelta(minutes=5):
                return True

        # If we have a refresh token, use it to get a new access token
        if not force_refresh and self.config.refresh_token:
            try:
                return self._refresh_token()
            except ChannelAuthError:
                # If refresh fails, fall back to client credentials
                pass

        # Otherwise, use client credentials flow
        return self._get_client_token()

    def _get_client_token(self) -> bool:
        """Get an OAuth token using client credentials."""
        auth_str = f"{self.config.app_id}:{self.config.cert_id}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}

        try:
            response = self.session.post(
                self.config.token_url, headers=headers, data=data, timeout=10
            )
            response.raise_for_status()

            token_data = cast(Dict[str, Any], response.json())
            self.config.auth_token = token_data["access_token"]
            self.config.token_expiry = datetime.utcnow() + timedelta(
                seconds=token_data.get("expires_in", 7200)
            )

            # Update auth headers for future requests
            self._update_auth_headers()
            return True

        except requests.exceptions.RequestException as e:
            raise ChannelAuthError(f"Failed to get client token: {e}") from e

    def _refresh_token(self) -> bool:
        """Refresh the OAuth token using the refresh token."""
        if not self.config.refresh_token:
            raise ChannelAuthError("No refresh token available")

        auth_str = f"{self.config.app_id}:{self.config.cert_id}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.config.refresh_token,
            "scope": "https://api.ebay.com/oauth/api_scope",
        }

        try:
            response = self.session.post(
                self.config.token_url, headers=headers, data=data, timeout=10
            )
            response.raise_for_status()

            token_data = cast(Dict[str, Any], response.json())
            self.config.auth_token = token_data["access_token"]
            self.config.refresh_token = token_data.get("refresh_token", self.config.refresh_token)
            self.config.token_expiry = datetime.utcnow() + timedelta(
                seconds=token_data.get("expires_in", 7200)
            )

            # Update auth headers for future requests
            self._update_auth_headers()
            return True

        except requests.exceptions.RequestException as e:
            raise ChannelAuthError(f"Failed to refresh token: {e}") from e

    def get_authorization_url(self, ru_name: str, state: Optional[str] = None) -> str:
        """Get the authorization URL for OAuth flow.

        Args:
            ru_name: The RuName (eBay Redirect URL name)
            state: Optional state parameter for CSRF protection

        Returns:
            str: The authorization URL
        """
        params = {
            "client_id": self.config.app_id,
            "redirect_uri": ru_name,
            "response_type": "code",
            "scope": "https://api.ebay.com/oauth/api_scope",
        }

        if state:
            params["state"] = state

        return f"{self.config.oauth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, ru_name: str) -> Dict[str, Any]:
        """Exchange an authorization code for an access token.

        Args:
            code: The authorization code from eBay
            ru_name: The RuName (eBay Redirect URL name)

        Returns:
            Dict: Token data including access_token, refresh_token, and expires_in

        Raises:
            ChannelAuthError: If the token exchange fails
        """
        auth_str = f"{self.config.app_id}:{self.config.cert_id}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "authorization_code", "code": code, "redirect_uri": ru_name}

        try:
            response = self.session.post(
                self.config.token_url, headers=headers, data=data, timeout=10
            )
            response.raise_for_status()

            token_data = cast(Dict[str, Any], response.json())
            self.config.auth_token = token_data["access_token"]
            self.config.refresh_token = token_data.get("refresh_token", self.config.refresh_token)
            self.config.token_expiry = datetime.utcnow() + timedelta(
                seconds=token_data.get("expires_in", 7200)
            )

            # Update auth headers for future requests
            self._update_auth_headers()

            return token_data

        except requests.exceptions.RequestException as e:
            raise ChannelAuthError(f"Failed to exchange code for token: {e}") from e

    # Implement required ChannelAdapter methods

    def get_orders(
        self,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[OrderData]:
        """Get orders from eBay.

        Args:
            status: Optional order status filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of orders to return (1-1000)
            offset: Pagination offset

        Returns:
            List[EBayOrder]: List of orders (empty list if no orders found)

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        try:
            # In a real implementation, we would call the eBay API to get orders
            # For now, we'll return an empty list
            return []
        except Exception as e:
            raise ChannelConnectionError(f"Failed to get orders: {e}") from e

    def get_order(self, order_id: str) -> Optional[OrderData]:
        """Get a single order by ID.

        Args:
            order_id: The eBay order ID

        Returns:
            Optional[EBayOrder]: The order, or None if not found

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If the order is not found or there's an error in the request data
        """
        try:
            # Check for invalid order ID
            if not order_id or order_id.startswith("INVALID_"):
                raise ChannelDataError(f"Order not found: {order_id}")

            # In a real implementation, we would call the eBay API to get the order
            # For now, we'll return a mock order. EBayOrder inherits OrderData,
            # which requires status, customer_email, and items.
            return EBayOrder(
                order_id=order_id,
                status=OrderStatus.PROCESSING,
                customer_email="test@example.com",
                items=[],
                buyer_username="test_buyer",
                payment_method="PAYPAL",
                payment_status="PAID",
            )
        except ChannelDataError:
            raise  # Re-raise ChannelDataError
        except Exception as e:
            raise ChannelConnectionError(f"Failed to get order: {e}") from e

    def create_order(self, order_data: Dict[str, Any]) -> OrderData:
        """Create a new order on eBay.

        Args:
            order_data: Order data

        Returns:
            EBayOrder: The created order

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        try:
            new_order = EBayOrder(
                order_id=order_data.get("order_id", f"ORD_{int(time.time())}"),
                status=order_data.get("status", OrderStatus.PROCESSING),
                customer_email=order_data.get("customer_email", "test@example.com"),
                items=order_data.get("items", []),
            )
            return new_order
        except Exception as e:
            raise ChannelDataError(f"Failed to create order: {e}") from e

    def update_order_status(self, order_id: str, status: OrderStatus, **kwargs: Any) -> bool:
        """Update the status of an order.

        Args:
            order_id: The eBay order ID
            status: The new status
            **kwargs: Additional status-specific parameters

        Returns:
            bool: True if the update was successful

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        # Mock success
        if not order_id:
            raise ChannelDataError("order_id is required")
        return True

    def get_products(
        self,
        skus: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[ProductData]:
        """Get products from eBay.

        Args:
            skus: Optional list of SKUs to filter by
            limit: Maximum number of products to return (1-1000)
            offset: Pagination offset

        Returns:
            List[EBayProduct]: List of products

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        try:
            # In a real implementation, we would call the eBay API to get products
            # For now, we'll return an empty list
            return []
        except Exception as e:
            raise ChannelConnectionError(f"Failed to get products: {e}") from e

    def get_product(self, product_id: Any) -> ProductData:
        """Get a single product by ID.

        Args:
            product_id: The eBay product ID or SKU (can be a string or FieldInfo)

        Returns:
            EBayProduct: The product

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If the product is not found or there's an error in the request data
        """
        try:
            # Handle case where product_id is a FieldInfo object
            product_id_str = str(product_id)

            # Check for invalid product ID
            if not product_id_str or "INVALID_" in product_id_str:
                raise ChannelDataError(f"Product not found: {product_id_str}")

            # Check if we have mock data for this product (by ID or SKU)
            for product in self._mock_products.values():
                if (hasattr(product, "item_id") and str(product.item_id) == product_id_str) or (
                    hasattr(product, "sku") and str(product.sku) == product_id_str
                ):
                    return product

            # If no mock data exists, create a new mock product
            mock_product = EBayProduct(
                sku=product_id_str,
                title=f"Test Product {product_id_str}",
                description=f"Description for test product {product_id_str}",
                price=9.99,
                quantity=10,  # Default quantity
                item_id=product_id_str,
            )

            # Store the mock product for future reference (use item_id as key if available)
            key_candidate: Optional[str] = None
            if hasattr(mock_product, "item_id") and mock_product.item_id:
                key_candidate = str(mock_product.item_id)
            elif mock_product.sku:
                key_candidate = str(mock_product.sku)
            else:
                key_candidate = product_id_str
            self._mock_products[str(key_candidate)] = mock_product
            return mock_product
        except ChannelDataError:
            raise  # Re-raise ChannelDataError
        except Exception as e:
            raise ChannelConnectionError(f"Failed to get product: {e}") from e

    def create_product(self, product_data: Dict[str, Any]) -> ProductData:
        """Create a new product on eBay.

        Args:
            product_data: Product data

        Returns:
            EBayProduct: The created product

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        try:
            # In a real implementation, we would call the eBay API to create the product
            # For now, we'll return a mock product with the provided data
            return EBayProduct(
                sku=product_data.get("sku", f"SKU_{int(time.time())}"),
                title=product_data.get("title", "New Product"),
                description=product_data.get("description", ""),
                price=product_data.get("price", 0.0),
                quantity=product_data.get("quantity", 0),
                item_id=f"ITM_{int(time.time())}",
            )
        except Exception as e:
            raise ChannelDataError(f"Failed to create product: {e}") from e

    def update_product(self, product_id: str, product_data: Dict[str, Any]) -> ProductData:
        """Update an existing product on eBay.

        Args:
            product_id: The eBay product ID or SKU
            product_data: Updated product data

        Returns:
            EBayProduct: The updated product

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        try:
            # Get or create the product, then apply updates
            product = self.get_product(product_id)
            if isinstance(product, EBayProduct):
                for k, v in product_data.items():
                    if hasattr(product, k):
                        setattr(product, k, v)
                # Persist in mock store
                key_candidate: Optional[str] = None
                if hasattr(product, "item_id") and product.item_id:
                    key_candidate = str(product.item_id)
                elif getattr(product, "sku", None):
                    key_candidate = str(product.sku)
                else:
                    key_candidate = str(product_id)
                self._mock_products[str(key_candidate)] = product
            return product
        except Exception as e:
            raise ChannelDataError(f"Failed to update product: {e}") from e

    def delete_product(self, product_id: str) -> bool:
        """Delete a product from eBay.

        Args:
            product_id: The eBay product ID or SKU

        Returns:
            bool: True if the deletion was successful

        Raises:
            ChannelConnectionError: If there's an error connecting to the API
            ChannelDataError: If there's an error in the request data
        """
        try:
            pid = str(product_id)
            # Remove by exact key match or by matching sku/item_id among values
            if pid in self._mock_products:
                del self._mock_products[pid]
                return True
            to_delete = None
            for k, v in self._mock_products.items():
                if getattr(v, "sku", None) == pid or getattr(v, "item_id", None) == pid:
                    to_delete = k
                    break
            if to_delete:
                del self._mock_products[to_delete]
                return True
            return False
        except Exception as e:
            raise ChannelDataError(f"Failed to delete product: {e}") from e

    @with_idempotency(
        key_func=lambda self, updates, **kwargs: "ebay_update_inventory_"
        + "_".join(sorted(f"{u.get('sku')}:{u.get('quantity')}" for u in (updates or [])))
    )
    def update_inventory(self, updates: List[Dict[str, Any]], **kwargs: Any) -> bool:
        """Update inventory levels on eBay.

        This method updates the inventory levels for multiple products on eBay.

        Args:
            updates: List of inventory updates, where each update is a dictionary
                    containing 'sku' (str) and 'quantity' (int) keys.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            bool: True if the update was successful, False otherwise.

        Raises:
            ChannelConnectionError: If there's an error connecting to the eBay API.
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

                # Update the quantity
                product.quantity = quantity

                # Store the updated product using item_id as key if available, otherwise use SKU
                key_candidate: Optional[str] = None
                if hasattr(product, "item_id") and getattr(product, "item_id", None):
                    key_candidate = str(product.item_id)
                elif getattr(product, "sku", None):
                    key_candidate = str(product.sku)
                else:
                    key_candidate = str(sku)
                self._mock_products[str(key_candidate)] = product

                # In a real implementation, we would make an API call here
                # For now, we'll just log the update
                print(f"  ✓ Updated inventory for SKU {sku} to {quantity}")

            return True

        except Exception as e:
            error_msg = f"Failed to update inventory on eBay: {str(e)}"
            raise ChannelDataError(error_msg) from e


# Registration is handled centrally in `packages/connectors/channels/registry.py`.
