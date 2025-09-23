"""Database package for MarketMind.

This package contains all database-related code including models, sessions, and utilities.
"""

from .base import Base, ScopedSession, SessionLocal, get_db, init_db
from .models import (
    Address,
    ChatbotInteraction,
    Customer,
    CustomerQuery,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    QueryPriority,
    QuerySource,
    QueryStatus,
    Supplier,
)

# Make important database utilities available at package level
__all__ = [
    "Base",
    "SessionLocal",
    "ScopedSession",
    "get_db",
    "init_db",
    "Product",
    "Customer",
    "Address",
    "Order",
    "OrderItem",
    "OrderStatus",
    "Supplier",
    "CustomerQuery",
    "ChatbotInteraction",
    "QueryStatus",
    "QueryPriority",
    "QuerySource",
]
