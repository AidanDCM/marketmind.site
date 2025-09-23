"""Supplier model for the MarketMind application."""

from datetime import datetime

# Import Product with TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

# Import Base from base.py to ensure all models use the same Base class
from .base import Base

if TYPE_CHECKING:
    from .product import Product


class Supplier(Base):
    """Supplier model representing product suppliers."""

    __tablename__ = "suppliers"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )  # Internal supplier code

    # Contact information
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Aliases expected by tests: allow Supplier(email=..., phone=...)
    email = synonym("contact_email")
    phone = synonym("contact_phone")

    # Business information
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tax_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # VAT, GST, etc.
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Address information
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Shipping and lead time
    lead_time_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Average lead time in days

    # Payment terms (in days)
    payment_terms: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Financial information
    credit_limit: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    current_balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    # Additional information
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, nullable=True, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="supplier", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, name='{self.name}')>"

    @property
    def full_address(self) -> str:
        """Get the full formatted address as a string."""
        parts = [
            self.company,
            self.contact_name,
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.postal_code}" if self.city and self.state else None,
            self.country,
        ]
        return "\n".join(filter(None, parts))

    @property
    def product_count(self) -> int:
        """Get the number of products from this supplier."""
        return len(self.products) if hasattr(self, "products") else 0

    def to_dict(self, include_products: bool = False) -> Dict[str, Any]:
        """Convert the supplier to a dictionary.

        Args:
            include_products: Whether to include the list of products

        Returns:
            Dictionary representation of the supplier
        """
        data = {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "company": self.company,
            "tax_number": self.tax_number,
            "website": self.website,
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
                "country": self.country,
            },
            "lead_time_days": self.lead_time_days,
            "payment_terms": self.payment_terms,
            "is_active": self.is_active,
            "is_approved": self.is_approved,
            "credit_limit": float(self.credit_limit) if self.credit_limit is not None else None,
            "current_balance": (
                float(self.current_balance) if self.current_balance is not None else 0.0
            ),
            "notes": self.notes,
            "meta": self.meta if self.meta else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }

        if include_products and hasattr(self, "products") and self.products is not None:
            data["products"] = [product.to_dict() for product in self.products]

        return data

    def update_lead_time(self, new_lead_time: int) -> None:
        """Update the supplier's lead time.

        Args:
            new_lead_time: The new lead time in days
        """
        self.lead_time_days = new_lead_time
        self.updated_at = datetime.utcnow()

    def get_contact_info(self) -> Dict[str, str]:
        """Get the supplier's contact information.

        Returns:
            Dictionary with contact information
        """
        return {
            "name": self.contact_name or self.company or self.name,
            "email": self.contact_email,
            "phone": self.contact_phone,
            "company": self.company,
        }
