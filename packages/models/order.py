"""Order and related models for MarketMind.

This module defines the Order, OrderItem, and related database models.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Session, relationship

from .base import Base


class OrderStatus(str, Enum):
    """Order status enumeration."""

    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    ON_HOLD = "on_hold"


class Order(Base):
    """Order model representing customer orders."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    channel_order_id = Column(String(100), index=True)  # External order ID from channel
    channel = Column(String(50), nullable=False, index=True)  # 'amazon', 'ebay', etc.

    # Customer information
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    customer_email = Column(String(255), index=True)

    # Order dates
    ordered_at = Column(DateTime, nullable=False, index=True)
    paid_at = Column(DateTime)
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)

    # Financials
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    shipping_amount = Column(Numeric(10, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)

    # Status
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)

    # Shipping information
    shipping_name = Column(String(100))
    shipping_company = Column(String(100))
    shipping_address1 = Column(String(255))
    shipping_address2 = Column(String(255))
    shipping_city = Column(String(100))
    shipping_state = Column(String(50))
    shipping_postal_code = Column(String(20), index=True)
    shipping_country = Column(String(2))  # ISO 3166-1 alpha-2
    shipping_phone = Column(String(20))

    # Billing information (could be same as shipping)
    billing_name = Column(String(100))
    billing_company = Column(String(100))
    billing_address1 = Column(String(255))
    billing_address2 = Column(String(255))
    billing_city = Column(String(100))
    billing_state = Column(String(50))
    billing_postal_code = Column(String(20))
    billing_country = Column(String(2))  # ISO 3166-1 alpha-2
    billing_phone = Column(String(20))

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_orders_channel_status", "channel", "status"),
        Index("idx_orders_customer", "customer_id"),
        Index("idx_orders_dates", "ordered_at"),
        CheckConstraint(
            "total = subtotal + tax_amount + shipping_amount - discount_amount",
            name="check_order_totals",
        ),
    )

    @property
    def item_count(self) -> int:
        """Get the total number of items in the order."""
        return sum(item.quantity for item in self.items)

    @classmethod
    def get_by_order_number(cls, db: Session, order_number: str) -> Optional["Order"]:
        """Get an order by its order number."""
        return db.query(cls).filter(cls.order_number == order_number).first()

    @classmethod
    def get_by_channel_order_id(
        cls, db: Session, channel: str, channel_order_id: str
    ) -> Optional["Order"]:
        """Get an order by its channel and channel order ID."""
        return (
            db.query(cls)
            .filter(cls.channel == channel, cls.channel_order_id == channel_order_id)
            .first()
        )

    def update_status(
        self, new_status: OrderStatus, commit: bool = False, db: Session = None
    ) -> None:
        """Update the order status and set appropriate timestamps."""
        self.status = new_status
        now = datetime.utcnow()

        if new_status == OrderStatus.PROCESSING and not self.paid_at:
            self.paid_at = now
        elif new_status == OrderStatus.SHIPPED and not self.shipped_at:
            self.shipped_at = now
        elif new_status == OrderStatus.DELIVERED and not self.delivered_at:
            self.delivered_at = now

        if commit and db:
            db.commit()


class OrderItem(Base):
    """Individual items within an order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id = Column(Integer, ForeignKey("products.id"), index=True)

    # Item details (snapshot at time of purchase)
    sku = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)

    # Channel-specific identifiers
    channel_item_id = Column(String(100), index=True)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    # Indexes
    __table_args__ = (
        Index("idx_order_items_sku", "sku"),
        CheckConstraint("quantity > 0", name="check_positive_quantity"),
        CheckConstraint(
            "total = (price * quantity) + tax_amount - discount_amount", name="check_item_totals"
        ),
    )

    @property
    def subtotal(self) -> Decimal:
        """Calculate the subtotal (price * quantity)."""
        return Decimal(str(self.price)) * self.quantity

    @property
    def total_with_tax(self) -> Decimal:
        """Calculate the total including tax."""
        return self.subtotal + Decimal(str(self.tax_amount))

    @property
    def total_after_discount(self) -> Decimal:
        """Calculate the total after applying discounts."""
        return self.total_with_tax - Decimal(str(self.discount_amount))
