"""
Channel listing and price history models.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import GUID, Base

if TYPE_CHECKING:
    # Forward references for type checking only
    from .listing import PriceHistory  # self-referential for type hints
    from .product import Product


class ChannelType(str, Enum):
    """Supported sales channels."""

    AMAZON = "amazon"
    EBAY = "ebay"
    WALMART = "walmart"
    SHOPIFY = "shopify"
    TIKTOK = "tiktok"
    ETSY = "etsy"
    WOOCOMMERCE = "woocommerce"
    BIGCOMMERCE = "bigcommerce"
    CUSTOM = "custom"


class FulfillmentType(str, Enum):
    """Fulfillment methods."""

    MFN = "mfn"  # Merchant Fulfilled
    FBA = "fba"  # Fulfilled by Amazon
    THREE_PL = "3pl"  # Third-party logistics
    DROPSHIP = "dropship"  # Dropshipping


class ListingStatus(str, Enum):
    """Listing status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    SUPPRESSED = "suppressed"  # Suppressed by channel for policy violations


class ChannelListing(Base):
    """Product listing on a sales channel."""

    __tablename__ = "channel_listing"

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

    # Channel details
    channel: Mapped[ChannelType] = mapped_column(
        String(20), nullable=False, index=True, comment="Sales channel"
    )
    listing_ref: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Channel's ID for this listing"
    )

    # Pricing
    price_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Current listing price in cents"
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", comment="ISO 4217 currency code"
    )

    # Fulfillment
    fulfillment: Mapped[FulfillmentType] = mapped_column(
        String(10),
        nullable=False,
        default=FulfillmentType.MFN,
        comment="How this product is fulfilled",
    )

    # Status
    status: Mapped[ListingStatus] = mapped_column(
        String(20), nullable=False, default=ListingStatus.DRAFT, comment="Listing status"
    )

    # Sync timestamps
    last_published_at: Mapped[Optional[datetime]] = mapped_column(
        comment="When this listing was last published to the channel"
    )
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(
        index=True, comment="When this listing was last checked/updated from the channel"
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="listings")
    price_history: Mapped[List["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="listing", lazy="selectin"
    )

    # Constraints
    __table_args__ = (
        # Ensure unique listing per channel
        UniqueConstraint("channel", "listing_ref", name="uq_channel_listing_ref"),
        # Index for common lookups
        Index("idx_channel_listing_product_channel", "product_id", "channel"),
        # Check constraints
        CheckConstraint("price_cents > 0", name="chk_listing_positive_price"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="chk_listing_valid_currency"),
    )

    @property
    def price(self) -> Decimal:
        """Get the price as a Decimal in dollars."""
        return Decimal(self.price_cents) / 100

    @property
    def current_price(self) -> Optional[Dict[str, Any]]:
        """Get the current price details from the most recent price history."""
        if not hasattr(self, "_current_price"):
            # This would be populated by a query that gets the latest price history
            # for this listing
            self._current_price = None
        return self._current_price


class PriceHistory(Base):
    """Historical price data for a channel listing.

    This table is partitioned by month for performance.
    """

    __tablename__ = "price_history"

    # Core fields
    org_id: Mapped[GUID] = mapped_column(
        GUID(),
        ForeignKey("org.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
        comment="Part of composite primary key for partitioning",
    )
    listing_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("channel_listing.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Price details
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, comment="Price in cents")
    buybox: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Whether this price won the buybox"
    )
    comp_best_cents: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Best competitor price in cents (if known)"
    )

    # Source and timing
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Source of this price (spapi, manual, keepa, etc.)"
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=text("now()"),
        comment="When this price was recorded",
    )

    # Additional metadata
    meta: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}", comment="Additional price metadata"
    )

    # Relationships
    listing: Mapped[ChannelListing] = relationship("ChannelListing", back_populates="price_history")

    # Constraints
    __table_args__ = (
        # Index for common lookups
        Index("idx_price_history_listing_recorded", "listing_id", "recorded_at"),
        # Check constraints
        CheckConstraint("price_cents > 0", name="chk_price_history_positive_price"),
        # PostgreSQL-specific configuration
        {
            "postgresql_partition_by": "RANGE (recorded_at)",
            # We'll handle the partition creation in a migration
        },
    )

    @property
    def price(self) -> Decimal:
        """Get the price as a Decimal in dollars."""
        return Decimal(self.price_cents) / 100

    @property
    def comp_best_price(self) -> Optional[Decimal]:
        """Get the best competitor price as a Decimal in dollars, if available."""
        return Decimal(self.comp_best_cents) / 100 if self.comp_best_cents else None
