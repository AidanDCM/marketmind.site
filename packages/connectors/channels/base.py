"""Base classes for channel adapters.

This module defines the base classes for channel adapters, which provide a
consistent interface for interacting with different e-commerce channels.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class OrderStatus(Enum):
    """Order status enumeration.

    Note: ACTIVE is a special status that can be used to filter for orders
    that are not in a terminal state (cancelled, refunded, failed, completed).
    It should not be used to set an order's status.
    """

    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ACTIVE = "active"  # Special status for filtering active orders


class ProductData:
    """Data class for product information."""

    def __init__(
        self,
        sku: str,
        title: str,
        description: str,
        price: float,
        quantity: int,
        **kwargs: Any,
    ):
        self.sku = sku
        self.title = title
        self.description = description
        self.price = price
        self.quantity = quantity
        self.extra_data = kwargs


class OrderData:
    """Data class for order information."""

    def __init__(
        self,
        order_id: str,
        status: OrderStatus,
        customer_email: str,
        items: List[Dict[str, Any]],
        **kwargs: Any,
    ):
        self.order_id = order_id
        self.status = status
        self.customer_email = customer_email
        self.items = items
        self.extra_data = kwargs


class ChannelAdapter(ABC):
    """Abstract base class for channel adapters.

        Channel adapters provide a consistent interface for interacting with
    different e-commerce channels.
    """

    #: The name of the channel (e.g., 'amazon', 'ebay')
    name: str = ""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize the channel adapter.

        Args:
            db_session: Optional SQLAlchemy database session
        """
        self.db = db_session

    @abstractmethod
    def authenticate(self, **kwargs: Any) -> bool:
        """Authenticate with the channel's API.

        Returns:
            bool: True if authentication was successful, False otherwise
        """
        pass

    @abstractmethod
    def get_orders(self, **kwargs: Any) -> List[OrderData]:
        """Retrieve orders from the channel.

        Returns:
            List[OrderData]: List of orders
        """
        pass

    @abstractmethod
    def get_products(self, **kwargs: Any) -> List[ProductData]:
        """Retrieve products from the channel.

        Returns:
            List[ProductData]: List of products
        """
        pass

    @abstractmethod
    def update_inventory(self, updates: List[Dict[str, Any]], **kwargs: Any) -> bool:
        """Update inventory levels on the channel.

        Args:
            updates: List of inventory updates, each containing 'sku' and 'quantity'

        Returns:
            bool: True if the update was successful, False otherwise
        """
        pass

    @abstractmethod
    def update_order_status(self, order_id: str, status: OrderStatus, **kwargs: Any) -> bool:
        """Update the status of an order on the channel.

        Args:
            order_id: The ID of the order to update
            status: The new status for the order

        Returns:
            bool: True if the update was successful, False otherwise
        """
        pass
