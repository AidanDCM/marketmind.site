"""
Order, order items, and fulfillment models.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import GUID, Base

if TYPE_CHECKING:
    # Forward reference for Product used in relationship annotations
    from .product import Product


class OrderStatus(str, Enum):
    """Order status lifecycle."""

    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"


class TaxModel(str, Enum):
    """Tax collection models."""

    MARKETPLACE_COLLECTED = "marketplace_collected"
    SELLER_COLLECTED = "seller_collected"
    TAX_EXEMPT = "tax_exempt"


class Order(Base):
    """Sales order from a channel."""

    __tablename__ = "order"

    # Core fields
    org_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("org.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brain_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("brain.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Channel and reference
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, comment="Sales channel"
    )
    order_ref: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="Channel's order reference"
    )

    # Buyer information (minimal PII)
    buyer: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        comment="Minimal buyer info (region/city/state only)",
    )
    ship_to_region: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Destination region for tax/fulfillment"
    )

    # Financials
    items_total_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Subtotal in cents (sum of item prices)"
    )
    shipping_total_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Shipping cost in cents"
    )
    tax_total_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Tax amount in cents"
    )
    tax_model: Mapped[TaxModel] = mapped_column(
        String(30),
        nullable=False,
        default=TaxModel.MARKETPLACE_COLLECTED,
        comment="How taxes are handled",
    )
    fees_total_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Total fees in cents"
    )
    net_revenue_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Net revenue in cents (items + shipping + tax - fees)"
    )

    # Status and timing
    status: Mapped[OrderStatus] = mapped_column(
        String(20),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
        comment="Current order status",
    )
    placed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, comment="When the order was placed"
    )

    # Relationships
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    fulfillments: Mapped[List["Fulfillment"]] = relationship("Fulfillment", back_populates="order")
    returns: Mapped[List["Return"]] = relationship("Return", back_populates="order")

    # Constraints
    __table_args__ = (
        # Ensure unique order reference per channel
        UniqueConstraint("channel", "order_ref", name="uq_order_channel_ref"),
        # Check constraints
        CheckConstraint("items_total_cents > 0", name="chk_order_positive_items_total"),
        CheckConstraint("shipping_total_cents >= 0", name="chk_order_non_negative_shipping"),
        CheckConstraint("tax_total_cents >= 0", name="chk_order_non_negative_tax"),
        CheckConstraint("fees_total_cents >= 0", name="chk_order_non_negative_fees"),
    )

    @property
    def total(self) -> Dict[str, Decimal]:
        """Get order totals as Decimal values."""
        return {
            "items": Decimal(self.items_total_cents) / 100,
            "shipping": Decimal(self.shipping_total_cents) / 100,
            "tax": Decimal(self.tax_total_cents) / 100,
            "fees": Decimal(self.fees_total_cents) / 100,
            "net_revenue": Decimal(self.net_revenue_cents) / 100,
        }


class OrderItem(Base):
    """Line item within an order."""

    __tablename__ = "order_item"

    # Core fields
    order_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("order.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[GUID] = mapped_column(
        GUID(),
        ForeignKey("product.id"),
        nullable=True,
        index=True,  # Allow for deleted products
    )

    # Product details
    sku: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Product SKU at time of order"
    )
    name: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Product name at time of order"
    )

    # Quantities
    qty: Mapped[int] = mapped_column(Integer, nullable=False, comment="Quantity ordered")

    # Financials
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, comment="Unit price in cents")
    tax_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Tax amount in cents"
    )
    fees_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Fees in cents"
    )
    cost_cents: Mapped[int] = mapped_column(Integer, nullable=False, comment="Unit cost in cents")
    est_ship_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Estimated shipping cost in cents"
    )

    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship("Product")

    # Constraints
    __table_args__ = (
        # Check constraints
        CheckConstraint("qty > 0", name="chk_order_item_positive_qty"),
        CheckConstraint("price_cents >= 0", name="chk_order_item_non_negative_price"),
        CheckConstraint("tax_cents >= 0", name="chk_order_item_non_negative_tax"),
        CheckConstraint("fees_cents >= 0", name="chk_order_item_non_negative_fees"),
        CheckConstraint("cost_cents >= 0", name="chk_order_item_non_negative_cost"),
        CheckConstraint("est_ship_cents >= 0", name="chk_order_item_non_negative_est_ship"),
    )

    @property
    def line_total(self) -> Decimal:
        """Calculate the line total (price * quantity) as Decimal."""
        return self.price * self.qty

    @property
    def price(self) -> Decimal:
        """Get the unit price as Decimal."""
        return Decimal(self.price_cents) / 100

    @property
    def tax(self) -> Decimal:
        """Get the tax amount as Decimal."""
        return Decimal(self.tax_cents) / 100

    @property
    def fees(self) -> Decimal:
        """Get the fees as Decimal."""
        return Decimal(self.fees_cents) / 100

    @property
    def cost(self) -> Decimal:
        """Get the unit cost as Decimal."""
        return Decimal(self.cost_cents) / 100

    @property
    def est_ship_cost(self) -> Decimal:
        """Get the estimated shipping cost as Decimal."""
        return Decimal(self.est_ship_cents) / 100


class FulfillmentStatus(str, Enum):
    """Fulfillment status."""

    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    FAILED = "failed"


class Fulfillment(Base):
    """Order fulfillment details."""

    __tablename__ = "fulfillment"

    # Core fields
    order_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("order.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Fulfillment details
    status: Mapped[FulfillmentStatus] = mapped_column(
        String(20), nullable=False, default=FulfillmentStatus.PENDING, index=True
    )
    carrier: Mapped[str] = mapped_column(String(100), nullable=True, comment="Shipping carrier")
    service: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="Shipping service level"
    )
    tracking_no: Mapped[str] = mapped_column(
        String(100), nullable=True, index=True, comment="Tracking number"
    )
    tracking_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Tracking URL"
    )

    # Timing
    shipped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When the order was shipped"
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When the order was delivered"
    )

    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="fulfillments")

    # Constraints
    __table_args__ = (
        # Ensure unique tracking number
        Index(
            "uq_fulfillment_tracking_no",
            "tracking_no",
            unique=True,
            postgresql_where=(tracking_no.isnot(None)),
        ),
    )


class ReturnStatus(str, Enum):
    """Return status."""

    REQUESTED = "requested"
    RECEIVED = "received"
    INSPECTING = "inspecting"
    APPROVED = "approved"
    REJECTED = "rejected"
    REFUNDED = "refunded"
    CLOSED = "closed"


class Return(Base):
    """Order return details."""

    __tablename__ = "return"

    # Core fields
    order_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("order.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Return details
    status: Mapped[ReturnStatus] = mapped_column(
        String(20), nullable=False, default=ReturnStatus.REQUESTED, index=True
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False, comment="Reason for return")
    rma_no: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, comment="Return Merchandise Authorization number"
    )
    refunded_cents: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Amount refunded in cents"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Additional notes")

    # Timing
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        comment="When the return was requested",
    )
    received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When the return was received"
    )

    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="returns")

    @property
    def refunded_amount(self) -> Optional[Decimal]:
        """Get the refunded amount as Decimal, if available."""
        return Decimal(self.refunded_cents) / 100 if self.refunded_cents else None
