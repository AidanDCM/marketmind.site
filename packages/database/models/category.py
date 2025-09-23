"""Category model for the MarketMind application."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import Base from base.py to ensure all models use the same Base class
from .base import Base

if TYPE_CHECKING:
    from .product import Product


class Category(Base):
    """Category model for product categorization."""

    __tablename__ = "categories"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Category details
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Hierarchy
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )

    # Metadata
    image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    meta: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category", remote_side=[id], back_populates="children", uselist=False
    )

    children: Mapped[List["Category"]] = relationship(
        "Category", back_populates="parent", lazy="dynamic"
    )

    products: Mapped[List["Product"]] = relationship(
        "Product", secondary="product_categories", back_populates="categories"
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"

    @property
    def full_path(self) -> str:
        """Return the full category path from root to this category."""
        if self.parent:
            from typing import cast as _cast

            return f"{self.parent.full_path} > {_cast(str, self.name)}"
        from typing import cast as _cast

        return _cast(str, self.name)
