"""Customer model for MarketMind.

This module defines the Customer model and related database operations.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Session, relationship

from .base import Base


class Customer(Base):
    """Customer model representing individuals who place orders."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)

    # Basic information
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))

    # Account information
    is_guest = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime)

    # Marketing preferences
    accepts_marketing = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    addresses = relationship("Address", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")

    # Indexes
    __table_args__ = (
        Index("idx_customers_email", "email"),
        Index("idx_customers_name", "last_name", "first_name"),
    )

    @property
    def full_name(self) -> str:
        """Get the customer's full name."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @classmethod
    def get_by_email(cls, db: Session, email: str) -> Optional["Customer"]:
        """Get a customer by email address (case-insensitive)."""
        return db.query(cls).filter(cls.email.ilike(email)).first()

    def get_default_address(self) -> Optional["Address"]:
        """Get the customer's default address, if any."""
        for address in self.addresses:
            if address.is_default:
                return address
        return self.addresses[0] if self.addresses else None


class Address(Base):
    """Customer address model for shipping and billing addresses."""

    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True)
    customer_id = Column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Address information
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(100))
    address1 = Column(String(255), nullable=False)
    address2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    postal_code = Column(String(20), nullable=False, index=True)
    country = Column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    phone = Column(String(20))

    # Address type and defaults
    address_type = Column(String(20), default="shipping", nullable=False)  # 'shipping' or 'billing'
    is_default = Column(Boolean, default=False, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="addresses")

    # Indexes
    __table_args__ = (
        Index("idx_addresses_customer", "customer_id"),
        Index("idx_addresses_country", "country"),
        Index("idx_addresses_postal", "postal_code"),
    )

    @property
    def full_name(self) -> str:
        """Get the full name for this address."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @property
    def formatted_address(self) -> str:
        """Get a formatted address string."""
        lines = []
        if self.company:
            lines.append(self.company)
        if self.full_name:
            lines.append(self.full_name)
        lines.append(self.address1)
        if self.address2:
            lines.append(self.address2)
        lines.append(f"{self.city}, {self.state} {self.postal_code}")
        lines.append(self.country)
        return "\n".join(lines)
