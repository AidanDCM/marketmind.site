"""Amazon SP-API Channel Adapter.

This module provides an implementation of the ChannelAdapter interface for
Amazon's Selling Partner API (SP-API).
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy.orm import Session

from ...shared.spapi_client import SpapiClient, SpapiError
from ..http.backoff import retryable
from ..http.exceptions import HttpError, map_http_error
from ..http.ratelimit import get_rate_limiter
from ..idempotency import with_idempotency
from .base import ChannelAdapter, OrderData, OrderStatus, ProductData

logger = logging.getLogger(__name__)


class AmazonAdapter(ChannelAdapter):
    """Channel adapter for Amazon's Selling Partner API (SP-API)."""

    name = "amazon"

    def __init__(self, db_session: Optional[Session] = None, **kwargs: Any) -> None:
        """Initialize the Amazon SP-API adapter.

        Args:
            db_session: Optional SQLAlchemy database session
            **kwargs: Additional keyword arguments for SpapiClient, including:
                - client_id: Amazon SP-API client ID
                - client_secret: Amazon SP-API client secret
                - refresh_token: Amazon SP-API refresh token
                - marketplace_id: Amazon marketplace ID (e.g., 'ATVPDKIKX0DER' for US)
                - region: Amazon region (e.g., 'na', 'eu', 'fe')
        """
        super().__init__(db_session)

        # Extract marketplace_id from kwargs if provided
        self.marketplace_id = kwargs.pop("marketplace_id", None)

        # Initialize the SpapiClient with the remaining kwargs
        self.client = SpapiClient(**kwargs)

        # If marketplace_id was provided, set it on the client
        if self.marketplace_id:
            self.client.marketplace_id = self.marketplace_id
        self.rate_limiter = get_rate_limiter("amazon_sp_api")
        self._marketplace_id = kwargs.get("marketplace_id")

    def authenticate(self, **kwargs: Any) -> bool:
        """Authenticate with Amazon SP-API.

        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            # Test authentication by making a lightweight API call
            self.client._ensure_token()
            return True
        except (requests.RequestException, ValueError, KeyError) as e:
            logger.error("Amazon SP-API authentication failed", exc_info=True, error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error during Amazon SP-API authentication", exc_info=True, error=str(e))
            return False

    @retryable(exceptions=(requests.RequestException,), max_retries=3)
    def get_orders(
        self,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[OrderData]:
        """Retrieve orders from Amazon SP-API.

        Args:
            start_date: Only return orders updated after this date
            **kwargs: Additional parameters for the API call

        Returns:
            List[OrderData]: List of orders

        Raises:
            HttpError: If there's an error communicating with the API
        """
        try:
            self.rate_limiter.acquire()

            # Convert datetime to ISO 8601 format if provided
            if start_date:
                kwargs["LastUpdatedAfter"] = start_date.isoformat()
            if end_date:
                kwargs["LastUpdatedBefore"] = end_date.isoformat()

            # Get orders from Amazon SP-API
            orders_endpoint = f"{self.client._base_url()}/orders/v0/orders"
            headers = self.client._base_headers()
            params: Dict[str, Any] = {
                "MarketplaceIds": self._marketplace_id or self.client.marketplace_id,
                **kwargs,
            }

            response = requests.get(orders_endpoint, headers=headers, params=params, timeout=30)
            # Raise to trigger retry on transient errors (429/5xx)
            response.raise_for_status()

            orders_data = response.json().get("payload", {}).get("Orders", [])
            return [self._normalize_order(order) for order in orders_data]

        except requests.RequestException as e:
            raise map_http_error(e) from e
        except SpapiError as e:
            raise HttpError(f"Amazon SP-API error: {str(e)}") from e

    @retryable(exceptions=(requests.RequestException,), max_retries=3)
    def get_order(self, order_id: str, **kwargs: Any) -> Optional[OrderData]:
        """Retrieve a single order by ID.

        Args:
            order_id: The Amazon order ID
            **kwargs: Additional parameters for the API call

        Returns:
            Optional[OrderData]: The order, or None if not found

        Raises:
            HttpError: If there's an error communicating with the API
        """
        try:
            self.rate_limiter.acquire()

            # Get order from Amazon SP-API
            order_endpoint = f"{self.client._base_url()}/orders/v0/orders/{order_id}"
            headers = self.client._base_headers()

            response = requests.get(order_endpoint, headers=headers, timeout=30)

            if response.status_code == 404:
                return None

            # Raise to trigger retry on transient errors (429/5xx)
            response.raise_for_status()

            order_data = response.json().get("payload", {})
            return self._normalize_order(order_data)

        except requests.RequestException as e:
            raise map_http_error(e) from e
        except SpapiError as e:
            raise HttpError(f"Amazon SP-API error: {str(e)}") from e

    def get_products(
        self,
        skus: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[ProductData]:
        """Retrieve products from Amazon SP-API.

        Args:
            **kwargs: Additional arguments to pass to the SP-API

        Returns:
            List[ProductData]: List of products

        Raises:
            HttpError: If there's an error communicating with the API
        """
        try:
            # TODO: Implement product retrieval from SP-API
            # This is a placeholder implementation
            return []
        except SpapiError as e:
            logger.error(f"Error getting products from Amazon: {e}")
            raise map_http_error(e) from e

    def update_inventory(self, updates: List[Dict[str, Any]], **kwargs: Any) -> bool:
        """Update inventory levels on Amazon SP-API.

        Args:
            updates: List of inventory updates, each containing 'sku' and 'quantity'
            **kwargs: Additional arguments to pass to the SP-API

        Returns:
            bool: True if the update was successful, False otherwise

        Raises:
            HttpError: If there's an error communicating with the API
        """
        try:
            # TODO: Implement inventory update in SP-API
            # This is a placeholder implementation
            for update in updates:
                logger.info(f"Updating inventory for SKU {update['sku']} to {update['quantity']}")
            return True
        except SpapiError as e:
            logger.error(f"Error updating inventory on Amazon: {e}")
            raise map_http_error(e) from e

    def update_order_status(self, order_id: str, status: OrderStatus, **kwargs: Any) -> bool:
        """Update the status of an order on Amazon SP-API.

        Args:
            order_id: The ID of the order to update
            status: The new status for the order
            **kwargs: Additional arguments to pass to the SP-API

        Returns:
            bool: True if the update was successful, False otherwise

        Raises:
            HttpError: If there's an error communicating with the API
        """
        try:
            # TODO: Implement order status update in SP-API
            # This is a placeholder implementation
            logger.info(f"Updating order {order_id} status to {status.value}")
            return True
        except SpapiError as e:
            logger.error(f"Error updating order status on Amazon: {e}")
            raise map_http_error(e) from e

    @with_idempotency(key_func=lambda *args, **kwargs: f"amazon_update_price_{kwargs.get('sku')}")
    @retryable(exceptions=(requests.RequestException,), max_retries=3)
    def update_price(self, sku: str, price: Decimal, **kwargs: Any) -> bool:
        """Update the price of a product on Amazon.

        Args:
            sku: The SKU of the product to update
            price: The new price
            **kwargs: Additional parameters for the API call

        Returns:
            bool: True if the update was successful, False otherwise

        Raises:
            HttpError: If there's an error communicating with the API
        """
        try:
            self.rate_limiter.acquire()

            # Prepare the price update payload
            payload = [
                {
                    "sku": sku,
                    "price": {"currency": kwargs.get("currency", "USD"), "amount": str(price)},
                }
            ]

            # Submit the price update
            endpoint = f"{self.client._base_url()}/catalog/2022-04-01/items/pricing"
            headers = {**self.client._base_headers(), "Content-Type": "application/json"}

            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            # Raise to trigger retry on transient errors (429/5xx)
            response.raise_for_status()

            return True

        except requests.RequestException as e:
            raise map_http_error(e) from e
        except SpapiError as e:
            raise HttpError(f"Amazon SP-API error: {str(e)}") from e

    def _normalize_order(self, order_data: Dict[str, Any]) -> OrderData:
        """Normalize Amazon order data to our OrderData model.

        Args:
            order_data: Raw order data from Amazon SP-API

        Returns:
            OrderData: Normalized order data
        """
        # Map Amazon order status to our OrderStatus enum
        status_map = {
            "Pending": OrderStatus.PENDING,
            "Unshipped": OrderStatus.PROCESSING,
            "PartiallyShipped": OrderStatus.PROCESSING,
            "Shipped": OrderStatus.SHIPPED,
            "Canceled": OrderStatus.CANCELLED,
            "Unfulfillable": OrderStatus.FAILED,
            "Delivered": OrderStatus.DELIVERED,
        }

        status = status_map.get(order_data.get("OrderStatus", ""), OrderStatus.PENDING)

        # Extract order items
        items = []
        for item in order_data.get("OrderItems", []):
            items.append(
                {
                    "sku": item.get("SellerSKU", ""),
                    "title": item.get("Title", ""),
                    "quantity": int(item.get("QuantityOrdered", 0)),
                    "price": Decimal(str(item.get("ItemPrice", {}).get("Amount", "0.00"))),
                    "total": Decimal(str(item.get("ItemPrice", {}).get("Amount", "0.00")))
                    * int(item.get("QuantityOrdered", 0)),
                }
            )

        # Create and return normalized order data
        return OrderData(
            order_id=order_data.get("AmazonOrderId", ""),
            status=status,
            customer_email=order_data.get("BuyerInfo", {}).get("BuyerEmail", ""),
            items=items,
            created_at=order_data.get("PurchaseDate"),
            updated_at=order_data.get("LastUpdateDate"),
            extra_data={
                "marketplace_id": order_data.get("MarketplaceId"),
                "shipping_address": order_data.get("ShippingAddress", {}),
                "payment_method": order_data.get("PaymentMethod"),
            },
        )

    def _get_competitive_pricing(self, asins: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get competitive pricing information for a list of ASINs.

        Args:
            asins: List of ASINs to get pricing for

        Returns:
            Dict mapping ASINs to their pricing information
        """
        try:
            self.rate_limiter.acquire()
            from typing import cast as _cast

            return _cast(Dict[str, Dict[str, Any]], self.client.get_competitive_pricing(asins))
        except Exception as e:
            logger.error(f"Failed to get competitive pricing: {str(e)}")
            return {}

    def get_competitive_pricing(self, asins: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get competitive pricing information for a list of ASINs.

        This is a wrapper around the SpapiClient method that handles rate limiting
        and error handling.

        Args:
            asins: List of ASINs to get pricing for

        Returns:
            Dict mapping ASINs to their pricing information
        """
        return self._get_competitive_pricing(asins)

    def health(self) -> Dict[str, Any]:
        """Return health status for the Amazon adapter."""
        try:
            # Validate credentials/session
            self.client._ensure_token()
            return {
                "ok": True,
                "name": self.name,
                "marketplace_id": self._marketplace_id or self.client.marketplace_id,
            }
        except Exception as e:
            return {"ok": False, "name": self.name, "error": str(e)}
