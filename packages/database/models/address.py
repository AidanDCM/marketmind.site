"""Address model for the MarketMind application."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .customer import Customer


class Address(Base):
    """Address model for customer addresses."""

    __tablename__ = "addresses"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key - using string reference to avoid circular import
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE", name="fk_address_customer_id"),
        nullable=False,
        index=True,
    )

    # Compatibility alias used by tests: allow Address(street=...) to set address_line1
    @property
    def street(self) -> str:
        # Cast to str for type checkers as SQLAlchemy descriptors may appear as Any
        from typing import cast as _cast

        return _cast(str, self.address_line1)

    @street.setter
    def street(self, value: str) -> None:
        self.address_line1 = value

    # Address information
    first_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    company: Mapped[Optional[str]] = mapped_column(nullable=True)
    address_line1: Mapped[str] = mapped_column(nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(nullable=True)
    city: Mapped[str] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column(nullable=False)
    postal_code: Mapped[str] = mapped_column(nullable=False)
    country: Mapped[str] = mapped_column(nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Address type
    is_default_shipping: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_default_billing: Mapped[bool] = mapped_column(default=False, nullable=False)
    # Unified default flag used by tests; maps to shipping default by convention
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship to Customer - using string reference to avoid circular import
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="addresses", foreign_keys=[customer_id], lazy="selectin"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the address to a dictionary."""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company": self.company,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "phone": self.phone,
            "is_default_shipping": self.is_default_shipping,
            "is_default_billing": self.is_default_billing,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __str__(self) -> str:
        """String representation of the address."""
        parts = [
            f"{self.first_name} {self.last_name}",
            self.company,
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.postal_code}",
            self.country,
        ]
        return ", ".join(filter(None, parts))
