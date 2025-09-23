from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class ChannelListing:
    """Lightweight ChannelListing used by mapping tests.

    This is not a SQLAlchemy model. It provides enough fields for
    tests in tests/connectors/test_mapping.py and mapping.denormalize_listing().
    """

    org_id: str
    sku: str
    price: Decimal = Decimal("0.00")
    currency: str = "USD"
    quantity_available: int = 0
    channel_product_id: Optional[str] = None
