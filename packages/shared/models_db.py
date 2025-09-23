from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.shared.db import Base


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), index=True)
    asin: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(512))
    brand: Mapped[Optional[str]] = mapped_column(String(128))
    images: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    supplier_offers: Mapped[list[SupplierOffer]] = relationship(back_populates="product")
    competitors: Mapped[list[Competitor]] = relationship(back_populates="product")
    price_history: Mapped[list[PriceHistory]] = relationship(back_populates="product")
    pricing_simulations: Mapped[list["PricingSimulation"]] = relationship(back_populates="product")

    __table_args__ = (UniqueConstraint("sku", name="uq_products_sku"),)


class ChannelListing(Base):
    __tablename__ = "channel_listings"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(32), index=True)  # amazon|ebay|walmart|shopify
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    listing_ref: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")  # draft|active|paused
    price: Mapped[Optional[float]] = mapped_column(Float)
    shipping_rule: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True
    )

    product: Mapped[Product] = relationship()

    __table_args__ = (Index("ix_channel_listings_prod_channel", "product_id", "channel"),)


class SupplierOffer(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_name: Mapped[str] = mapped_column(String(128), index=True)
    supplier_sku: Mapped[str] = mapped_column(String(128), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    cost: Mapped[float] = mapped_column(Float)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)
    lead_time_hours: Mapped[int] = mapped_column(Integer, default=48)
    ships_from: Mapped[Optional[str]] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, default=None)

    product: Mapped[Product] = relationship(back_populates="supplier_offers")

    __table_args__ = (
        Index("ix_suppliers_product_supplier", "product_id", "supplier_name"),
        UniqueConstraint("supplier_name", "supplier_sku", name="uq_supplier_sku"),
    )


class Competitor(Base):
    __tablename__ = "competitors"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(32), index=True)  # amazon|ebay|walmart
    asin: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    seller: Mapped[Optional[str]] = mapped_column(String(128))
    price: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    product: Mapped[Product] = relationship(back_populates="competitors")

    __table_args__ = (Index("ix_competitors_product_channel", "product_id", "channel"),)


class PriceHistory(Base):
    __tablename__ = "price_history"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(32))
    price: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(64))  # competitor|ours|simulation
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    product: Mapped[Product] = relationship(back_populates="price_history")


class Sale(Base):
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(64), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    channel: Mapped[str] = mapped_column(String(32), index=True)
    sale_price: Mapped[float] = mapped_column(Float)
    fees: Mapped[float] = mapped_column(Float, default=0.0)
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    product: Mapped[Optional[Product]] = relationship()


class PricingSimulation(Base):
    __tablename__ = "pricing_simulations"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    proposed_price: Mapped[float] = mapped_column(Float)
    margin_pct: Mapped[float] = mapped_column(Float)
    inputs: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    status: Mapped[str] = mapped_column(
        String(32), default="pending", index=True
    )  # pending|approved|rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    product: Mapped[Product] = relationship(back_populates="pricing_simulations")


class IngestCheckpoint(Base):
    __tablename__ = "ingest_checkpoints"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    brain_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    pipeline: Mapped[str] = mapped_column(String(32), index=True)  # orders|signals|catalog
    source: Mapped[str] = mapped_column(String(32), index=True)  # channel or supplier
    key: Mapped[Optional[str]] = mapped_column(String(64), index=True)  # e.g., bucket id
    value: Mapped[Optional[str]] = mapped_column(String(64))  # ISO8601 or other scalar
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "org_id", "brain_id", "pipeline", "source", "key", name="uq_ingest_ckpt_scope"
        ),
    )
