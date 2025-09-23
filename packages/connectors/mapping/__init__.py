"""Data mapping utilities for converting between vendor APIs and canonical models.

This module provides functions for normalizing data from different vendor APIs
into our canonical data models, and vice versa.
"""

from .normalize import (
    # normalize_inventory,  # Temporarily disabled until InventoryEvent model is available
    denormalize_listing,
    normalize_customer,
    normalize_order,
    normalize_product,
)

__all__ = [
    "normalize_product",
    "normalize_order",
    "normalize_customer",
    # 'normalize_inventory',  # Temporarily disabled until InventoryEvent model is available
    "denormalize_listing",
    # 'denormalize_price_update',  # Not implemented yet
    # 'denormalize_inventory_update',  # Not implemented yet
]
