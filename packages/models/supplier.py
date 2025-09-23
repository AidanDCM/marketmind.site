"""Supplier and related models for MarketMind.

This module defines the Supplier, SupplierOffer, and related database models.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Session, relationship

from .base import Base


class SupplierStatus(str, Enum):
    """Supplier status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_HOLD = "on_hold"
    PENDING = "pending_approval"


class Supplier(Base):
    """Supplier model representing product suppliers and vendors."""

    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(20), unique=True, index=True)  # Short code for reference

    # Contact information
    contact_name = Column(String(100))
    contact_email = Column(String(255), index=True)
    contact_phone = Column(String(20))

    # Status
    status = Column(SQLEnum(SupplierStatus), default=SupplierStatus.ACTIVE, nullable=False)

    # Additional metadata
    metadata_ = Column("metadata", JSON, default=dict)  # For supplier-specific data

    # Relationships
    offers = relationship("SupplierOffer", back_populates="supplier", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_suppliers_code", "code"),
        Index("idx_suppliers_status", "status"),
    )

    @classmethod
    def get_by_code(cls, db: Session, code: str) -> Optional["Supplier"]:
        """Get a supplier by its code."""
        return db.query(cls).filter(cls.code == code).first()

    def get_offer_for_product(self, product_id: int) -> Optional["SupplierOffer"]:
        """Get the supplier's offer for a specific product, if any."""
        for offer in self.offers:
            if offer.product_id == product_id:
                return offer
        return None


class SupplierOffer(Base):
    """Represents a supplier's offer for a specific product."""

    __tablename__ = "supplier_offers"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(
        Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Supplier's product information
    supplier_sku = Column(String(100), nullable=False, index=True)
    supplier_product_name = Column(String(255))

    # Pricing and availability
    cost_price = Column(Numeric(10, 2), nullable=False)
    min_order_quantity = Column(Integer, default=1, nullable=False)
    lead_time_days = Column(Integer, default=1, nullable=False)  # Days to ship
    is_available = Column(Boolean, default=True, nullable=False)

    # Additional metadata
    metadata_ = Column("metadata", JSON, default=dict)  # For offer-specific data

    # Relationships
    supplier = relationship("Supplier", back_populates="offers")
    product = relationship("Product", back_populates="supplier_offers")

    # Indexes
    __table_args__ = (
        Index("idx_supplier_offers_supplier_product", "supplier_id", "product_id", unique=True),
        Index("idx_supplier_offers_sku", "supplier_sku"),
        Index("idx_supplier_offers_available", "is_available"),
        CheckConstraint("cost_price > 0", name="check_positive_cost"),
        CheckConstraint("min_order_quantity > 0", name="check_positive_min_qty"),
    )

    @property
    def total_cost(self, quantity: int = 1) -> Decimal:
        """Calculate the total cost for a given quantity."""
        return Decimal(str(self.cost_price)) * max(quantity, self.min_order_quantity)

    @classmethod
    def get_by_supplier_sku(
        cls, db: Session, supplier_id: int, supplier_sku: str
    ) -> Optional["SupplierOffer"]:
        """Get a supplier offer by supplier ID and SKU."""
        return (
            db.query(cls)
            .filter(cls.supplier_id == supplier_id, cls.supplier_sku == supplier_sku)
            .first()
        )


class SupplierOrder(Base):
    """Represents an order placed with a supplier."""

    __tablename__ = "supplier_orders"

    class Status(str, Enum):
        DRAFT = "draft"
        PENDING = "pending"
        PROCESSING = "processing"
        SHIPPED = "shipped"
        DELIVERED = "delivered"
        CANCELLED = "cancelled"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(Status), default=Status.DRAFT, nullable=False)

    # Order details
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    expected_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)

    # Financials
    subtotal = Column(Numeric(10, 2), default=0, nullable=False)
    shipping_cost = Column(Numeric(10, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)

    # Tracking
    tracking_number = Column(String(100))
    tracking_url = Column(Text)

    # Relationships
    supplier = relationship("Supplier")
    items = relationship("SupplierOrderItem", back_populates="order", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_supplier_orders_supplier_status", "supplier_id", "status"),
        Index("idx_supplier_orders_dates", "order_date"),
    )

    @property
    def item_count(self) -> int:
        """Get the total number of items in the order."""
        return sum(item.quantity for item in self.items)

    def update_status(self, new_status: Status, commit: bool = False, db: Session = None) -> None:
        """Update the order status and set appropriate timestamps."""
        self.status = new_status
        now = datetime.utcnow()

        if new_status == self.Status.SHIPPED and not self.actual_delivery_date:
            self.actual_delivery_date = now

        if commit and db:
            db.commit()


class SupplierOrderItem(Base):
    """Individual items within a supplier order."""

    __tablename__ = "supplier_order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer, ForeignKey("supplier_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    supplier_offer_id = Column(Integer, ForeignKey("supplier_offers.id"), index=True)

    # Item details
    sku = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)

    # Relationships
    order = relationship("SupplierOrder", back_populates="items")
    product = relationship("Product")
    supplier_offer = relationship("SupplierOffer")

    # Indexes
    __table_args__ = (
        Index("idx_supplier_order_items_sku", "sku"),
        CheckConstraint("quantity > 0", name="check_positive_quantity"),
        CheckConstraint("unit_cost >= 0", name="check_non_negative_unit_cost"),
    )
