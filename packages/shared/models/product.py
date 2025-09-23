"""
Product, Supplier, and SupplierOffer models.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import GUID, Base

if TYPE_CHECKING:
    # Forward references for relationships
    from .listing import ChannelListing


class Product(Base):
    """Product model representing a sellable item."""

    __tablename__ = "product"

    # Core identifiers
    org_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("org.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brain_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("brain.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Internal stock keeping unit"
    )

    # External identifiers
    asin: Mapped[Optional[str]] = mapped_column(
        String(10), unique=True, index=True, comment="Amazon Standard Identification Number"
    )
    upc: Mapped[Optional[str]] = mapped_column(
        String(12), index=True, comment="Universal Product Code"
    )
    ean: Mapped[Optional[str]] = mapped_column(
        String(13), index=True, comment="European Article Number"
    )

    # Product details
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    category: Mapped[Optional[str]] = mapped_column(
        String(100), index=True, comment="Primary product category"
    )

    # Physical attributes
    weight_g: Mapped[Optional[int]] = mapped_column(Integer, comment="Weight in grams")
    dim_cm: Mapped[Dict[str, float]] = mapped_column(
        JSONB, comment="Dimensions in cm: {length, width, height}"
    )

    # Extended attributes
    attrs: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}", comment="Additional product attributes"
    )

    # Relationships
    supplier_offers: Mapped[List["SupplierOffer"]] = relationship(
        "SupplierOffer", back_populates="product", lazy="selectin"
    )
    listings: Mapped[List["ChannelListing"]] = relationship(
        "ChannelListing", back_populates="product", lazy="selectin"
    )

    # Constraints
    __table_args__ = (
        # Ensure unique SKU per brain
        UniqueConstraint("org_id", "brain_id", "sku", name="uq_product_org_brain_sku"),
        # Add GIN index for JSONB fields
        Index("idx_product_attrs_gin", "attrs", postgresql_using="gin"),
        # Add GIN index for text search
        Index(
            "idx_product_fts",
            "title",
            "brand",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops", "brand": "gin_trgm_ops"},
        ),
        # Check constraints
        CheckConstraint("weight_g IS NULL OR weight_g > 0", name="chk_product_weight_positive"),
        CheckConstraint(
            "(dim_cm->>'length')::numeric > 0 AND "
            "(dim_cm->>'width')::numeric > 0 AND "
            "(dim_cm->>'height')::numeric > 0",
            name="chk_product_dimensions_positive",
        ),
    )

    @property
    def current_price(self) -> Optional[Decimal]:
        """Get the current price from the most recent price history."""
        if not hasattr(self, "_current_price"):
            # This would be populated by a query that joins with price_history
            # and gets the latest price for this product
            self._current_price = None
        return self._current_price


class Supplier(Base):
    """Supplier model representing product vendors."""

    __tablename__ = "supplier"

    # Core fields
    org_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("org.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Supplier's primary region (NA, EU, ASIA, etc.)"
    )

    # API and integration details
    api_ref: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        comment="API reference data (tokens, endpoints, etc.)",
    )

    # Relationships
    offers: Mapped[List["SupplierOffer"]] = relationship(
        "SupplierOffer", back_populates="supplier", lazy="selectin"
    )

    # Constraints
    __table_args__ = (
        # Ensure unique name per org
        UniqueConstraint("org_id", "name", name="uq_supplier_org_name"),
    )


class SupplierOffer(Base):
    """Supplier's offer for a specific product."""

    __tablename__ = "supplier_offer"

    # Core fields
    org_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("org.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brain_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("brain.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("supplier.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Supplier-specific details
    supplier_sku: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Supplier's SKU for this product"
    )
    cost_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Cost per unit in cents"
    )
    stock: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Current stock level"
    )
    lead_time_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=7, comment="Estimated lead time in days"
    )
    map_cents: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Minimum Advertised Price in cents (if applicable)"
    )

    # Warehouse and location info
    warehouse: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}", comment="Warehouse location codes and details"
    )

    # Sync and status
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        index=True, comment="When this offer was last synced from the supplier"
    )

    # Relationships
    product: Mapped[Product] = relationship("Product", back_populates="supplier_offers")
    supplier: Mapped[Supplier] = relationship("Supplier", back_populates="offers")

    # Constraints
    __table_args__ = (
        # Ensure unique supplier+SKU combination
        UniqueConstraint("supplier_id", "supplier_sku", name="uq_supplier_offer_supplier_sku"),
        # Check constraints
        CheckConstraint("cost_cents > 0", name="chk_supplier_offer_positive_cost"),
        CheckConstraint("stock >= 0", name="chk_supplier_offer_non_negative_stock"),
        CheckConstraint("lead_time_days >= 0", name="chk_supplier_offer_lead_time"),
    )

    @property
    def cost(self) -> Decimal:
        """Get the cost as a Decimal in dollars."""
        return Decimal(self.cost_cents) / 100

    @property
    def map_price(self) -> Optional[Decimal]:
        """Get the MAP price as a Decimal in dollars, if set."""
        return Decimal(self.map_cents) / 100 if self.map_cents else None
