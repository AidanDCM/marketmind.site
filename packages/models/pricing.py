"""Pricing models for MarketMind.

This module defines models related to pricing, including price history, competitive pricing,
and buy box data.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Session, relationship

from .base import Base


class PriceSource(str, Enum):
    """Source of price information."""

    MANUAL = "manual"  # Manually set by user
    CHANNEL = "channel"  # From sales channel (Amazon, eBay, etc.)
    COMPETITOR = "competitor"  # From competitor monitoring
    SUPPLIER = "supplier"  # From supplier price list
    PRICING_ENGINE = "pricing_engine"  # From automated pricing rules
    IMPORT = "import"  # Imported from external source


class PriceHistory(Base):
    """Historical pricing data for products."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    # Pricing information
    cost_price = Column(Numeric(10, 2))
    list_price = Column(Numeric(10, 2))
    sale_price = Column(Numeric(10, 2))

    # Source of this price data
    source = Column(SQLEnum(PriceSource), nullable=False, index=True)
    source_id = Column(String(100), index=True)  # External ID from the source

    # Additional metadata
    metadata_ = Column("metadata", JSON, default=dict)  # For source-specific data

    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    product = relationship("Product", back_populates="price_history")

    # Indexes
    __table_args__ = (
        Index("idx_price_history_product_recorded", "product_id", "recorded_at", unique=True),
        Index("idx_price_history_source", "source", "source_id"),
    )

    @classmethod
    def get_latest_for_product(
        cls, db: Session, product_id: int, source: Optional[PriceSource] = None
    ) -> Optional["PriceHistory"]:
        """Get the latest price history entry for a product, optionally filtered by source."""
        query = db.query(cls).filter(cls.product_id == product_id)

        if source:
            query = query.filter(cls.source == source)

        return query.order_by(cls.recorded_at.desc()).first()

    @classmethod
    def get_price_trend(
        cls, db: Session, product_id: int, days: int = 30, source: Optional[PriceSource] = None
    ) -> List[Dict[str, Any]]:
        """Get price trend data for a product over time."""

        from sqlalchemy import text

        # This is a simplified example - you might need to adjust based on your database
        # and specific requirements for how to aggregate/group the data

        query = """
        SELECT 
            DATE(recorded_at) as date,
            AVG(sale_price) as avg_price,
            MIN(sale_price) as min_price,
            MAX(sale_price) as max_price,
            COUNT(*) as data_points
        FROM price_history
        WHERE 
            product_id = :product_id
            AND recorded_at >= DATE('now', '-' || :days || ' days')
            {source_filter}
        GROUP BY DATE(recorded_at)
        ORDER BY date
        """

        params = {"product_id": product_id, "days": days}

        if source:
            query = query.replace("{source_filter}", "AND source = :source")
            params["source"] = source.value if isinstance(source, Enum) else source
        else:
            query = query.replace("{source_filter}", "")

        result = db.execute(text(query), params)

        return [
            {
                "date": row.date.isoformat(),
                "avg_price": float(row.avg_price) if row.avg_price else None,
                "min_price": float(row.min_price) if row.min_price else None,
                "max_price": float(row.max_price) if row.max_price else None,
                "data_points": row.data_points,
            }
            for row in result
        ]


class CompetitiveOffer(Base):
    """Competitive offer data from marketplaces."""

    __tablename__ = "competitive_offers"

    class OfferType(str, Enum):
        MERCHANT = "merchant"  # Regular merchant offer
        FBA = "fba"  # Fulfilled by Amazon
        FBM = "fbm"  # Fulfilled by merchant
        BUY_BOX = "buy_box"  # Current buy box winner
        BUY_BOX_ELIGIBLE = "eligible"  # Eligible for buy box

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    # Offer details
    seller_id = Column(String(100), index=True)
    seller_name = Column(String(255))
    offer_type = Column(SQLEnum(OfferType), nullable=False, index=True)

    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    shipping_price = Column(Numeric(10, 2), default=0, nullable=False)
    is_fulfilled_by_amazon = Column(Boolean, default=False, nullable=False)

    # Offer conditions
    is_buy_box_winner = Column(Boolean, default=False, nullable=False, index=True)
    is_featured_merchant = Column(Boolean, default=False, nullable=False)
    is_prime = Column(Boolean, default=False, nullable=False)

    # Additional metadata
    condition = Column(String(50))  # 'New', 'Used', 'Refurbished', etc.
    feedback_count = Column(Integer)
    positive_feedback_rating = Column(Numeric(5, 2))  # Percentage

    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    product = relationship("Product")

    # Indexes
    __table_args__ = (
        Index("idx_competitive_offers_product_seller", "product_id", "seller_id"),
        Index("idx_competitive_offers_buy_box", "product_id", "is_buy_box_winner"),
        Index("idx_competitive_offers_price", "product_id", "price"),
    )

    @property
    def total_price(self) -> Decimal:
        """Calculate the total price including shipping."""
        return Decimal(str(self.price)) + Decimal(str(self.shipping_price or 0))

    @classmethod
    def get_buy_box_winner(cls, db: Session, product_id: int) -> Optional["CompetitiveOffer"]:
        """Get the current buy box winner for a product, if any."""
        return (
            db.query(cls)
            .filter(cls.product_id == product_id, cls.is_buy_box_winner == True)  # noqa: E712
            .order_by(cls.recorded_at.desc())
            .first()
        )

    @classmethod
    def get_lowest_offer(
        cls,
        db: Session,
        product_id: int,
        fba_only: bool = False,
        min_feedback: int = 0,
        min_rating: float = 0,
    ) -> Optional["CompetitiveOffer"]:
        """Get the lowest priced offer for a product, with optional filters."""
        query = db.query(cls).filter(cls.product_id == product_id)

        if fba_only:
            query = query.filter(cls.is_fulfilled_by_amazon == True)  # noqa: E712

        if min_feedback > 0:
            query = query.filter(cls.feedback_count >= min_feedback)

        if min_rating > 0:
            query = query.filter(cls.positive_feedback_rating >= min_rating)

        return query.order_by(
            (cls.price + cls.shipping_price).asc(), cls.recorded_at.desc()
        ).first()


class BuyBoxHistory(Base):
    """Historical buy box ownership data."""

    __tablename__ = "buy_box_history"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    # Seller information
    seller_id = Column(String(100), index=True)
    seller_name = Column(String(255))

    # Pricing at time of winning buy box
    price = Column(Numeric(10, 2), nullable=False)
    shipping_price = Column(Numeric(10, 2), default=0, nullable=False)

    # Duration in buy box
    entered_at = Column(DateTime, nullable=False, index=True)
    exited_at = Column(DateTime, index=True)

    # Relationships
    product = relationship("Product")

    # Indexes
    __table_args__ = (
        Index("idx_buy_box_history_product", "product_id", "entered_at"),
        Index("idx_buy_box_history_seller", "seller_id", "entered_at"),
    )

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate the duration in the buy box in seconds, if exited."""
        if not self.exited_at:
            return None
        return (self.exited_at - self.entered_at).total_seconds()

    @classmethod
    def get_current_buy_box_owner(cls, db: Session, product_id: int) -> Optional["BuyBoxHistory"]:
        """Get the current buy box owner for a product, if any."""
        return (
            db.query(cls)
            .filter(cls.product_id == product_id, cls.exited_at.is_(None))
            .order_by(cls.entered_at.desc())
            .first()
        )

    @classmethod
    def get_buy_box_share(
        cls, db: Session, product_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Calculate buy box share by seller for a product over a date range."""
        # This is a simplified example - the actual implementation would need to handle
        # overlapping time periods and edge cases more carefully

        query = """
        WITH time_slots AS (
            SELECT 
                seller_id,
                seller_name,
                SUM(
                    EXTRACT(EPOCH FROM 
                        LEAST(COALESCE(exited_at, :end_date), :end_date) - 
                        GREATEST(entered_at, :start_date)
                    )
                ) as seconds_in_buy_box
            FROM buy_box_history
            WHERE 
                product_id = :product_id
                AND entered_at <= :end_date
                AND (exited_at >= :start_date OR exited_at IS NULL)
            GROUP BY seller_id, seller_name
        )
        SELECT 
            seller_id,
            seller_name,
            seconds_in_buy_box,
            seconds_in_buy_box / NULLIF(
                SUM(seconds_in_buy_box) OVER (), 0
            ) as share
        FROM time_slots
        ORDER BY seconds_in_buy_box DESC
        """

        result = db.execute(
            query, {"product_id": product_id, "start_date": start_date, "end_date": end_date}
        )

        return [
            {
                "seller_id": row.seller_id,
                "seller_name": row.seller_name,
                "seconds_in_buy_box": row.seconds_in_buy_box,
                "share": float(row.share) if row.share else 0.0,
            }
            for row in result
        ]
