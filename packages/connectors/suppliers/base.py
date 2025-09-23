"""Base protocol for supplier adapters.

This module defines the base protocol for supplier adapters, which provide a
consistent interface for interacting with different suppliers.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypedDict, runtime_checkable


class StockInfo(TypedDict):
    """Type definition for stock information."""

    stock: int
    lead_time_days: int
    updated_at: str  # ISO format datetime


class TrackingEvent(TypedDict):
    """Type definition for shipment tracking events."""

    event_time: str  # ISO format datetime
    status: str
    location: str
    description: str
    tracking_number: str


@runtime_checkable
class SupplierAdapter(Protocol):
    """Protocol defining the interface for supplier adapters.

    Supplier adapters provide a consistent interface for interacting with
    different suppliers.
    """

    #: The name of the supplier (e.g., 'cj_dropshipping', 'autods')
    name: str

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Check the health of the supplier connection.

        Returns:
            Dict containing health status, latency, and other metadata.
            Example: {
                'ok': bool,
                'latency_ms': float,
                'details': Dict[str, Any]
            }
        """
        ...

    @abstractmethod
    def sync_catalog_delta(self, *, org_id: str, brain_id: str) -> Dict[str, int]:
        """Synchronize product catalog and supplier offers.

        Args:
            org_id: The organization ID
            brain_id: The brain ID

        Returns:
            Dictionary with counts of products and offers processed.
            Example: {
                'products_created': int,
                'products_updated': int,
                'offers_created': int,
                'offers_updated': int,
                'skipped': int
            }
        """
        ...

    @abstractmethod
    def get_stock(self, supplier_sku: str, *, org_id: str, brain_id: str) -> StockInfo:
        """Get current stock and lead time information for a product.

        Args:
            supplier_sku: The supplier's SKU for the product
            org_id: The organization ID
            brain_id: The brain ID

        Returns:
            Dictionary containing stock and lead time information.
            Example: {
                'stock': 42,
                'lead_time_days': 3,
                'updated_at': '2023-01-01T12:00:00Z'
            }
        """
        ...

    @abstractmethod
    def place_order(self, po: Dict[str, Any], *, org_id: str, brain_id: str) -> Dict[str, str]:
        """Place a new purchase order with the supplier.

        Args:
            po: Purchase order details in standardized format
            org_id: The organization ID
            brain_id: The brain ID

        Returns:
            Dictionary containing the supplier's PO reference and status.
            Example: {
                'supplier_po_ref': 'PO12345',
                'status': 'received',
                'estimated_ship_date': '2023-01-10',  # Optional
                'order_total': 123.45  # Optional
            }
        """
        ...

    @abstractmethod
    def get_tracking(
        self, supplier_po_ref: str, *, org_id: str, brain_id: str
    ) -> List[TrackingEvent]:
        """Get tracking information for a purchase order.

        Args:
            supplier_po_ref: The supplier's PO reference
            org_id: The organization ID
            brain_id: The brain ID

        Returns:
            List of tracking events in chronological order.
            Example: [
                {
                    'event_time': '2023-01-05T10:30:00Z',
                    'status': 'shipped',
                    'location': 'Warehouse A',
                    'description': 'Package has left the warehouse',
                    'tracking_number': '1Z999AA1234567890'
                },
                ...
            ]
        """
        ...


class SupplierError(Exception):
    """Base exception for supplier-related errors."""

    pass


class SupplierAuthError(SupplierError):
    """Raised when authentication with the supplier fails."""

    pass


class SupplierRateLimitError(SupplierError):
    """Raised when rate limited by the supplier's API."""

    def __init__(self, retry_after: Optional[float] = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after = retry_after  # Optional: seconds until rate limit resets


class SupplierServerError(SupplierError):
    """Raised for 5xx errors from the supplier's API."""

    pass


class SupplierClientError(SupplierError):
    """Raised for 4xx errors that aren't authentication or rate limit related."""

    pass


class SupplierValidationError(SupplierError):
    """Raised when request data fails validation."""

    pass
