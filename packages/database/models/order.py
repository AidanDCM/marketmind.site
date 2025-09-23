"""Order models for the MarketMind application."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

# Import Base from base.py to ensure all models use the same Base class
from .base import Base

if TYPE_CHECKING:
    from .address import Address
    from .customer import Customer
    from .product import Product


class OrderStatus(Enum):
    """Order status enumeration."""

    DRAFT = "draft"  # Order is being created
    PENDING = "pending"  # Order is placed but payment is pending
    PROCESSING = "processing"  # Payment received, order is being processed
    SHIPPED = "shipped"  # Order has been shipped
    DELIVERED = "delivered"  # Order has been delivered
    CANCELLED = "cancelled"  # Order has been cancelled
    REFUNDED = "refunded"  # Order has been refunded
    FAILED = "failed"  # Order failed (e.g., payment failed)
    ON_HOLD = "on_hold"  # Order is on hold
    COMPLETED = "completed"  # Order is completed (final state)


class PaymentStatus(Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    VOIDED = "voided"
    FAILED = "failed"


class FulfillmentStatus(Enum):
    """Fulfillment status enumeration."""

    UNFULFILLED = "unfulfilled"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    RESTOCKED = "restocked"


class Order(Base):
    """Order model representing customer orders."""

    __tablename__ = "orders"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Order identification
    @staticmethod
    def _default_order_number() -> str:
        return f"ORD-{int(datetime.utcnow().timestamp())}"

    order_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=True,
        default=lambda: Order._default_order_number(),
    )

    # Customer information
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True
    )  # Null for guest checkouts
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Order status
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, values_callable=lambda x: [e.value for e in x]),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, values_callable=lambda x: [e.value for e in x]),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    fulfillment_status: Mapped[FulfillmentStatus] = mapped_column(
        SQLEnum(FulfillmentStatus, values_callable=lambda x: [e.value for e in x]),
        default=FulfillmentStatus.UNFULFILLED,
        nullable=False,
    )

    # Order totals
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total_discounts: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total_shipping: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total_tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # total_amount property for float comparison in tests while persisting as Decimal
    @property
    def total_amount(self) -> float:
        return float(self.total) if self.total is not None else 0.0

    @total_amount.setter
    def total_amount(self, value: Optional[float]) -> None:
        self.total = Decimal(str(value)) if value is not None else Decimal("0.00")

    total_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total_refunded: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # Currency
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Billing and shipping information
    billing_address_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("addresses.id"), nullable=True
    )
    shipping_address_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("addresses.id"), nullable=True
    )

    # Shipping information
    shipping_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Payment information
    payment_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Order metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )  # IPv6 can be up to 45 chars
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referrer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional data
    meta: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, nullable=True, default=dict)
    private_meta: Mapped[Dict[str, Any]] = mapped_column(
        "private_metadata", JSON, nullable=True, default=dict
    )

    # Timestamps
    # Explicit order placement datetime (tests expect 'order_date')
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship(
        "Customer", back_populates="orders", foreign_keys=[customer_id]
    )
    billing_address: Mapped[Optional["Address"]] = relationship(
        "Address", foreign_keys=[billing_address_id]
    )
    shipping_address: Mapped[Optional["Address"]] = relationship(
        "Address", foreign_keys=[shipping_address_id]
    )
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint("total >= 0", name="check_order_total_positive"),
        CheckConstraint("total_paid >= 0", name="check_total_paid_positive"),
        CheckConstraint("total_refunded >= 0", name="check_total_refunded_positive"),
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status.value}')>"

    @property
    def item_count(self) -> int:
        """Get the total number of items in the order."""
        return sum(item.quantity for item in self.items) if self.items else 0

    @property
    def remaining_balance(self) -> Decimal:
        """Get the remaining balance to be paid."""
        total = cast(Decimal, self.total)
        paid = cast(Decimal, self.total_paid)
        remaining = total - paid
        return remaining if remaining > Decimal("0.00") else Decimal("0.00")

    def calculate_totals(self) -> None:
        """Calculate order totals based on items and adjustments."""
        self.subtotal = (
            sum(item.total_price for item in self.items) if self.items else Decimal("0.00")
        )
        self.total = self.subtotal + self.total_shipping + self.total_tax - self.total_discounts

    def add_item(
        self, product: "Product", quantity: int = 1, price: Optional[Decimal] = None
    ) -> "OrderItem":
        """Add an item to the order.

        Args:
            product: The product to add
            quantity: The quantity to add
            price: Optional custom price (for discounts/price overrides)

        Returns:
            The created OrderItem
        """
        item = OrderItem(
            order=self,
            product=product,
            product_name=product.name,
            sku=product.sku,
            quantity=quantity,
            price=price or product.price,
            original_price=product.price,
        )

        if self.items is None:
            self.items = []
        self.items.append(item)
        self.calculate_totals()
        return item

    def update_status(
        self, new_status: Union[OrderStatus, PaymentStatus], save: bool = True
    ) -> None:
        """Update the order status and set appropriate timestamps.

        Args:
            new_status: The new order status
            save: Whether to save the changes to the database
        """
        now = datetime.utcnow()

        # Update based on enum type
        if isinstance(new_status, PaymentStatus):
            self.payment_status = new_status
            if new_status == PaymentStatus.PAID:
                self.paid_at = self.paid_at or now
        else:
            # It's an OrderStatus
            self.status = new_status
            if new_status == OrderStatus.SHIPPED:
                self.shipped_at = self.shipped_at or now
            elif new_status == OrderStatus.DELIVERED:
                self.delivered_at = self.delivered_at or now
            elif new_status == OrderStatus.CANCELLED:
                self.cancelled_at = self.cancelled_at or now

        if save and self.id:
            from ..database import SessionLocal

            db = SessionLocal()
            try:
                db.add(self)
                db.commit()
            finally:
                db.close()

    def to_dict(self, include_items: bool = True, include_customer: bool = False) -> Dict[str, Any]:
        """Convert the order to a dictionary.

        Args:
            include_items: Whether to include order items
            include_customer: Whether to include customer details

        Returns:
            Dictionary representation of the order
        """
        result = {
            "id": self.id,
            "order_number": self.order_number,
            "status": self.status.value if self.status else None,
            "payment_status": self.payment_status.value if self.payment_status else None,
            "fulfillment_status": (
                self.fulfillment_status.value if self.fulfillment_status else None
            ),
            "customer_id": self.customer_id,
            "customer_email": self.customer_email,
            "subtotal": float(self.subtotal) if self.subtotal is not None else 0.0,
            "total_discounts": (
                float(self.total_discounts) if self.total_discounts is not None else 0.0
            ),
            "total_shipping": (
                float(self.total_shipping) if self.total_shipping is not None else 0.0
            ),
            "total_tax": float(self.total_tax) if self.total_tax is not None else 0.0,
            "total": float(self.total) if self.total is not None else 0.0,
            "total_paid": float(self.total_paid) if self.total_paid is not None else 0.0,
            "total_refunded": (
                float(self.total_refunded) if self.total_refunded is not None else 0.0
            ),
            "currency": self.currency,
            "item_count": self.item_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }

        if include_items and self.items:
            result["items"] = [item.to_dict() for item in self.items]

        if include_customer and self.customer:
            result["customer"] = self.customer.to_dict()

        if self.billing_address:
            result["billing_address"] = self.billing_address.to_dict()

        if self.shipping_address:
            result["shipping_address"] = self.shipping_address.to_dict()

        return result


class OrderItem(Base):
    """Order item model representing individual items within an order."""

    __tablename__ = "order_items"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Relationships
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=True
    )  # Null if product is deleted

    # Product information (denormalized for historical accuracy)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # Actual price paid
    # Alias to match tests using unit_price
    unit_price = synonym("price")
    original_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # Original price at time of purchase

    # Quantity
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Discounts
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    # Taxes
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=0, nullable=False
    )  # Tax rate as decimal (e.g., 0.2 for 20%)

    # Additional data
    variant: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # For product variants
    meta: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, nullable=True, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship("Product")

    @property
    def total_price(self) -> Decimal:
        """Calculate the total price for this line item (price * quantity)."""
        return cast(Decimal, self.price) * Decimal(str(self.quantity))

    @property
    def total_discount(self) -> Decimal:
        """Calculate the total discount for this line item."""
        return cast(Decimal, self.discount_amount) * Decimal(str(self.quantity))

    @property
    def total_tax(self) -> Decimal:
        """Calculate the total tax for this line item."""
        return cast(Decimal, self.tax_amount) * Decimal(str(self.quantity))

    def to_dict(self) -> Dict[str, Any]:
        """Convert the order item to a dictionary."""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "sku": self.sku,
            "price": float(self.price) if self.price is not None else 0.0,
            "original_price": (
                float(self.original_price) if self.original_price is not None else 0.0
            ),
            "quantity": self.quantity,
            "total_price": float(self.total_price) if self.total_price is not None else 0.0,
            "discount_amount": (
                float(self.discount_amount) if self.discount_amount is not None else 0.0
            ),
            "tax_amount": float(self.tax_amount) if self.tax_amount is not None else 0.0,
            "tax_rate": float(self.tax_rate) if self.tax_rate is not None else 0.0,
            "variant": self.variant,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
