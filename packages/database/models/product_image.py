"""Product Image model for the MarketMind application."""

from datetime import datetime

# Import with TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .product import Product


class ProductImage(Base):
    """Product Image model representing images associated with products."""

    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to the product
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)

    # Image details
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    alt_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship
    product: Mapped["Product"] = relationship("Product", back_populates="images")

    def __repr__(self) -> str:
        return f"<ProductImage(id={self.id}, product_id={self.product_id}, is_primary={self.is_primary})>"

    def to_dict(self) -> dict:
        """Convert the product image to a dictionary."""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "alt_text": self.alt_text,
            "is_primary": self.is_primary,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
