"""Product-Category association model for the MarketMind application."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Table

from .base import Base

# Association table for many-to-many relationship between products and categories
product_categories = Table(
    "product_categories",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
    Column("is_primary", Boolean, default=False, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
    Column(
        "updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    ),
)
