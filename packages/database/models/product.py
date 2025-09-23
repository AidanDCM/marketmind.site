"""Product model for the MarketMind application."""

import time
from datetime import datetime
from decimal import Decimal

# Import with TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import Session as _SASession

# Import Base from base.py to ensure all models use the same Base class
from .base import Base

if TYPE_CHECKING:
    from .category import Category
    from .order import OrderItem
    from .pricing import PricingSnapshot
    from .product_attribute import ProductAttribute
    from .product_image import ProductImage
    from .product_review import ProductReview
    from .supplier import Supplier


class Product(Base):
    """Product model representing items in the marketplace."""

    __tablename__ = "products"

    # Primary key (Python-side default so id exists before flush)
    @staticmethod
    def _default_id() -> int:
        return int(time.time() * 1_000_000)

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False, default=_default_id
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Ensure ID is assigned immediately so tests can read product.id before flush
        if "id" not in kwargs or kwargs.get("id") is None:
            kwargs["id"] = Product._default_id()
        super().__init__(*args, **kwargs)

    # Core product information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    cost_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Product identification
    upc: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    ean: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    isbn: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    # Product details
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in grams
    length: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in cm
    width: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in cm
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in cm

    # Categorization (keep optional FK + many-to-many via product_categories)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )
    category: Mapped[Optional["Category"]] = relationship("Category")

    # Relationships
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=True
    )
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", back_populates="products")
    pricing_snapshots: Mapped[List["PricingSnapshot"]] = relationship(
        "PricingSnapshot", back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")

    # Inventory tracking
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Product status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_physical: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # Digital vs physical product

    # Digital product fields
    download_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    download_limit: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Max downloads per customer

    # Product metadata
    meta: Mapped[Dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=True, default=dict
    )  # Flexible field for additional data

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships (continued)
    images: Mapped[List["ProductImage"]] = relationship(
        "ProductImage", back_populates="product", cascade="all, delete-orphan"
    )
    attributes: Mapped[List["ProductAttribute"]] = relationship(
        "ProductAttribute", back_populates="product", cascade="all, delete-orphan"
    )
    reviews: Mapped[List["ProductReview"]] = relationship(
        "ProductReview", back_populates="product", cascade="all, delete-orphan"
    )
    categories: Mapped[List["Category"]] = relationship(
        "Category", secondary="product_categories", back_populates="products"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"

    @property
    def stock_status(self) -> str:
        """Get the stock status of the product."""
        if self.quantity <= 0:
            return "out_of_stock"
        elif self.quantity <= 10:  # Assuming 10 is the threshold for low stock
            return "low_stock"
        return "in_stock"

    def update_inventory(self, quantity: int, action: str = "add") -> None:
        """Update the product inventory.

        Args:
            quantity: The quantity to add or remove
            action: Either 'add' or 'remove'
        """
        if action == "add":
            self.quantity += quantity
        elif action == "remove":
            if self.quantity < quantity:
                raise ValueError("Insufficient stock")
            self.quantity -= quantity
        else:
            raise ValueError("Invalid action. Must be 'add' or 'remove'")

    def get_price_with_tax(self, tax_rate: float = 0.0) -> Decimal:
        """Get the price including tax.

        Args:
            tax_rate: The tax rate as a decimal (e.g., 0.2 for 20%)

        Returns:
            The price including tax
        """
        return round(Decimal(str(self.price)) * (1 + Decimal(str(tax_rate))), 2)

    def to_dict(self) -> dict:
        """Convert the product to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "description": self.description,
            "price": float(self.price) if self.price is not None else None,
            "cost_price": float(self.cost_price) if self.cost_price is not None else None,
            "quantity": self.quantity,
            "stock_status": self.stock_status,
            "brand": self.brand,
            "model": self.model,
            "weight": self.weight,
            "dimensions": {
                "length": self.length,
                "width": self.width,
                "height": self.height,
            },
            "supplier_id": self.supplier_id,
            "category_id": self.category_id,
            "is_active": bool(self.is_active),
            "is_featured": bool(self.is_featured),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Ensure that when a Product has category_id set, the many-to-many association is kept in sync
def _sync_product_category(session: _SASession, flush_context: Any, instances: Any) -> None:
    from .category import Category  # local import to avoid circulars at import time

    # Iterate over new and dirty objects in this session
    for obj in list(session.new) + list(session.dirty):
        if isinstance(obj, Product):
            # If a category_id is present, make sure corresponding association exists
            if obj.category_id is not None:
                # Try using loaded category if available; else fetch it
                cat = obj.category or session.get(Category, obj.category_id)
                if cat is not None and cat not in obj.categories:
                    obj.categories.append(cat)


# Register the before_flush listener once at import time
event.listen(_SASession, "before_flush", _sync_product_category, retval=False)
