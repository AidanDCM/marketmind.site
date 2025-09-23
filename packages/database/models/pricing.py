"""Pricing data models for MarketMind.

This module contains models for tracking product pricing data over time,
including competitor pricing, historical trends, and pricing experiments.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .product import Product


class PricingSource(str, Enum):
    """Source of pricing data."""

    AMAZON = "amazon"
    WALMART = "walmart"
    TARGET = "target"
    SHOPIFY = "shopify"
    MANUAL = "manual"
    API = "api"
    WEB_SCRAPER = "web_scraper"


class PricingTier(str, Enum):
    """Pricing tiers for products."""

    BUDGET = "budget"
    STANDARD = "standard"
    PREMIUM = "premium"
    LUXURY = "luxury"


class PricingSnapshot(BaseModel):
    """Represents a snapshot of pricing data for a product."""

    __tablename__ = "pricing_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    source: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )  # Optional in tests

    # Price information
    base_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    sale_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    # Aliases expected by tests
    price: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    is_on_sale: Mapped[bool] = mapped_column(Boolean, default=False)

    # Inventory information
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    stock_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Shipping information
    free_shipping: Mapped[bool] = mapped_column(Boolean, default=False)
    shipping_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Competitor information (if applicable)
    competitor_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    competitor_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Dict] = mapped_column(
        "metadata", JSON, default=dict
    )  # Using metadata_ to avoid conflict with SQLAlchemy's metadata
    competitor_prices: Mapped[Dict] = mapped_column(JSON, default=dict)

    # Timestamps
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product", back_populates="pricing_snapshots", foreign_keys=[product_id]
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Preserve explicit product_id passed by callers (tests use this)
        pid = kwargs.get("product_id", None)
        super().__init__(*args, **kwargs)
        if pid is not None:
            self.product_id = pid

    experiments: Mapped[List["PricingExperiment"]] = relationship(
        "PricingExperiment", back_populates="pricing_snapshot", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        UniqueConstraint("product_id", "source", "captured_at", name="_product_source_time_uc"),
    )

    def to_dict(self) -> Dict:
        """Convert the pricing snapshot to a dictionary."""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "source": self.source,
            "base_price": float(self.base_price) if self.base_price is not None else None,
            "sale_price": float(self.sale_price) if self.sale_price is not None else None,
            "price": float(self.price) if self.price is not None else None,
            "cost": float(self.cost) if self.cost is not None else None,
            "currency": self.currency,
            "is_on_sale": bool(self.is_on_sale),
            "in_stock": bool(self.in_stock),
            "stock_quantity": self.stock_quantity,
            "free_shipping": bool(self.free_shipping),
            "shipping_cost": float(self.shipping_cost) if self.shipping_cost is not None else None,
            "competitor_name": self.competitor_name,
            "competitor_url": self.competitor_url,
            "notes": self.notes,
            "metadata": self.metadata_ or {},
            "competitor_prices": self.competitor_prices or {},
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PricingExperiment(BaseModel):
    """Represents a pricing experiment or A/B test."""

    __tablename__ = "pricing_experiments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Experiment configuration
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Pricing configuration
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    test_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Experiment groups
    control_group_size: Mapped[int] = mapped_column(Integer, default=1000)
    test_group_size: Mapped[int] = mapped_column(Integer, default=1000)

    # Results
    control_group_conversion: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # Percentage
    test_group_conversion: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # Percentage
    confidence_level: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # 0-100
    p_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 6), nullable=True
    )  # Statistical significance

    # Relationships
    pricing_snapshot_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pricing_snapshots.id"), nullable=True
    )
    pricing_snapshot: Mapped[Optional["PricingSnapshot"]] = relationship(
        "PricingSnapshot", back_populates="experiments"
    )

    # Metadata
    metadata_: Mapped[Dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> Dict:
        """Convert the pricing experiment to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": bool(self.is_active),
            "base_price": float(self.base_price) if self.base_price is not None else None,
            "test_price": float(self.test_price) if self.test_price is not None else None,
            "sample_size": self.sample_size,
            "traffic_allocation": self.traffic_allocation,
            "control_group_conversion": (
                float(self.control_group_conversion)
                if self.control_group_conversion is not None
                else None
            ),
            "test_group_conversion": (
                float(self.test_group_conversion)
                if self.test_group_conversion is not None
                else None
            ),
            "confidence_level": (
                float(self.confidence_level) if self.confidence_level is not None else None
            ),
            "p_value": float(self.p_value) if self.p_value is not None else None,
            "pricing_snapshot_id": self.pricing_snapshot_id,
            "metadata": self.metadata_ or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
