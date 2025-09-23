"""Product model for MarketMind.

This module defines the Product model and related database operations.
"""

from typing import List, Optional

from sqlalchemy import Boolean, Column, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Session, relationship

from .base import Base


class Product(Base):
    """Product model representing items sold through MarketMind."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    asin = Column(String(10), index=True)  # Amazon Standard Identification Number
    upc = Column(String(12), index=True)  # Universal Product Code
    title = Column(String(500), nullable=False)
    description = Column(Text)
    brand = Column(String(100))
    category = Column(String(100))

    # Dimensions and weight
    weight_oz = Column(Numeric(10, 2))
    length_in = Column(Numeric(10, 2))
    width_in = Column(Numeric(10, 2))
    height_in = Column(Numeric(10, 2))

    # Inventory tracking
    quantity_available = Column(Integer, default=0, nullable=False)
    quantity_reserved = Column(Integer, default=0, nullable=False)

    # Pricing
    cost_price = Column(Numeric(10, 2), nullable=False)
    list_price = Column(Numeric(10, 2), nullable=False)
    sale_price = Column(Numeric(10, 2))

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_variant = Column(Boolean, default=False, nullable=False)
    requires_shipping = Column(Boolean, default=True, nullable=False)

    # Relationships
    supplier_offers = relationship("SupplierOffer", back_populates="product")
    price_history = relationship("PriceHistory", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

    # Indexes
    __table_args__ = (
        Index("idx_products_sku", "sku"),
        Index("idx_products_asin", "asin"),
        Index("idx_products_upc", "upc"),
        Index("idx_products_active", "is_active"),
    )

    @property
    def quantity_on_hand(self) -> int:
        """Get the current on-hand quantity (available - reserved)."""
        return self.quantity_available - self.quantity_reserved

    @classmethod
    def get_by_sku(cls, db: Session, sku: str) -> Optional["Product"]:
        """Get a product by SKU."""
        return db.query(cls).filter(cls.sku == sku).first()

    @classmethod
    def get_by_asin(cls, db: Session, asin: str) -> List["Product"]:
        """Get all products with the given ASIN."""
        return db.query(cls).filter(cls.asin == asin).all()

    def update_inventory(self, available_delta: int = 0, reserved_delta: int = 0) -> None:
        """Update inventory levels.

        Args:
            available_delta: Change in available quantity (positive for increase, negative for decrease)
            reserved_delta: Change in reserved quantity (positive for increase, negative for decrease)
        """
        self.quantity_available += available_delta
        self.quantity_reserved += reserved_delta

        # Ensure we don't go negative
        self.quantity_available = max(0, self.quantity_available)
        self.quantity_reserved = max(0, self.quantity_reserved)

    def to_dict(self) -> dict:
        """Convert product to dictionary with additional computed fields."""
        data = super().to_dict()
        data["quantity_on_hand"] = self.quantity_on_hand
        return data
