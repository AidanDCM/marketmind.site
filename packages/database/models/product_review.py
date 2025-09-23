"""Product Review model for the MarketMind application."""

from datetime import datetime

# Import with TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .product import Product
    from .user import User


class ProductReview(Base):
    """Product Review model representing customer reviews for products."""

    __tablename__ = "product_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Review details
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-5 stars

    # Review status
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadata
    helpful_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    not_helpful_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Additional metadata
    meta: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, nullable=True, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<ProductReview(id={self.id}, product_id={self.product_id}, rating={self.rating})>"

    def to_dict(self) -> dict:
        """Convert the product review to a dictionary."""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "user_id": self.user_id,
            "title": self.title,
            "comment": self.comment,
            "rating": self.rating,
            "is_approved": self.is_approved,
            "is_verified_purchase": self.is_verified_purchase,
            "helpful_votes": self.helpful_votes,
            "not_helpful_votes": self.not_helpful_votes,
            "meta": self.meta,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
