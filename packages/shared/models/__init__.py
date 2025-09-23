"""
MarketMind Data Models

This module contains all SQLAlchemy models for the application.
"""

# Import all models to ensure they are registered with SQLAlchemy
from .audit import AuditLog, ConfigAudit, InventoryEvent
from .base import GUID, Base
from .listing import ChannelListing, PriceHistory
from .order import Fulfillment, Order, OrderItem, Return
from .org import BillingPlan, Brain, BrainStatus, Org, OrgStatus
from .product import Product, Supplier, SupplierOffer

# This ensures that all models are loaded and registered with SQLAlchemy's metadata
__all__ = [
    "Base",
    "GUID",
    "Org",
    "Brain",
    "OrgStatus",
    "BillingPlan",
    "BrainStatus",
    "Product",
    "Supplier",
    "SupplierOffer",
    "ChannelListing",
    "PriceHistory",
    "Order",
    "OrderItem",
    "Fulfillment",
    "Return",
    "AuditLog",
    "ConfigAudit",
    "InventoryEvent",
]
