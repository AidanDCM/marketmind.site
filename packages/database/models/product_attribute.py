"""Product Attribute model for the MarketMind application."""

from datetime import datetime

# Import with TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .product import Product


class ProductAttribute(Base):
    """Product Attribute model representing attributes associated with products."""

    __tablename__ = "product_attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to the product
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)

    # Attribute details
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    display_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # text, number, color, etc.
    is_variant: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )  # If this attribute defines a variant
    is_visible: Mapped[bool] = mapped_column(
        default=True, nullable=False
    )  # If this attribute should be shown to customers

    # For variant attributes
    variant_ordering: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata
    meta: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, nullable=True, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship
    product: Mapped["Product"] = relationship("Product", back_populates="attributes")

    def __repr__(self) -> str:
        return f"<ProductAttribute(id={self.id}, name='{self.name}', product_id={self.product_id})>"

    def to_dict(self) -> dict:
        """Convert the product attribute to a dictionary."""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "name": self.name,
            "value": self.value,
            "display_name": self.display_name,
            "display_type": self.display_type,
            "is_variant": self.is_variant,
            "is_visible": self.is_visible,
            "variant_ordering": self.variant_ordering,
            "meta": self.meta,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
