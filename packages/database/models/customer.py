"""Customer model for the MarketMind application."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import JSON, ForeignKeyConstraint, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import Base from base.py to ensure all models use the same Base class
from .base import Base

if TYPE_CHECKING:
    from .address import Address
    from .order import Order


class Customer(Base):
    """Customer model representing marketplace customers."""

    __tablename__ = "customers"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Core customer information
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Account information
    password_hash: Mapped[Optional[str]] = mapped_column(nullable=True)  # Null for guest checkouts
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Foreign Keys
    default_shipping_address_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )

    default_billing_address_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )

    # Table arguments for foreign key constraints
    __table_args__ = (
        ForeignKeyConstraint(
            ["default_shipping_address_id"],
            ["addresses.id"],
            name="fk_customer_default_shipping_address",
            use_alter=True,
            initially="DEFERRED",
            deferrable=True,
        ),
        ForeignKeyConstraint(
            ["default_billing_address_id"],
            ["addresses.id"],
            name="fk_customer_default_billing_address",
            use_alter=True,
            initially="DEFERRED",
            deferrable=True,
        ),
    )

    # Customer metadata
    tax_exempt: Mapped[bool] = mapped_column(default=False, nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Additional data
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    addresses: Mapped[List["Address"]] = relationship(
        "Address",
        back_populates="customer",
        foreign_keys="Address.customer_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Default addresses (using viewonly to avoid circular dependency issues)
    default_shipping_address: Mapped[Optional["Address"]] = relationship(
        "Address",
        foreign_keys=[default_shipping_address_id],
        primaryjoin="Address.id == foreign(Customer.default_shipping_address_id)",
        viewonly=True,
    )

    default_billing_address: Mapped[Optional["Address"]] = relationship(
        "Address",
        foreign_keys=[default_billing_address_id],
        primaryjoin="Address.id == foreign(Customer.default_billing_address_id)",
        viewonly=True,
    )

    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="customer", lazy="selectin", viewonly=True
    )

    @property
    def full_name(self) -> str:
        """Get the customer's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def total_orders(self) -> int:
        """Get the total number of orders placed by this customer."""
        return len(self.orders) if hasattr(self, "orders") else 0

    @property
    def total_spent(self) -> float:
        """Get the total amount spent by this customer."""
        if not hasattr(self, "orders") or not self.orders:
            return 0.0
        return float(sum(order.total_paid or 0 for order in self.orders))

    def get_default_address(self, address_type: str = "shipping") -> Optional[Any]:
        """Get the default shipping or billing address.

        Args:
            address_type: Either 'shipping' or 'billing'

        Returns:
            The default address or None if not set
        """
        if address_type == "shipping":
            return self.default_shipping_address
        elif address_type == "billing":
            return self.default_billing_address
        return None

    def to_dict(
        self, include_orders: bool = False, include_addresses: bool = False
    ) -> Dict[str, Any]:
        """Convert the customer to a dictionary.

        Args:
            include_orders: Whether to include the customer's orders
            include_addresses: Whether to include the customer's addresses

        Returns:
            Dictionary representation of the customer
        """

        result = {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "total_orders": self.total_orders,
            "total_spent": self.total_spent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_addresses:
            result["addresses"] = (
                [addr.to_dict() for addr in self.addresses] if self.addresses else []
            )
            result["default_shipping_address"] = (
                self.default_shipping_address.to_dict() if self.default_shipping_address else None
            )
            result["default_billing_address"] = (
                self.default_billing_address.to_dict() if self.default_billing_address else None
            )

        if include_orders and hasattr(self, "orders"):
            result["orders"] = [order.to_dict() for order in self.orders]

        return result
