from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SupplierOfferItem:
    supplier_name: str
    supplier_sku: str
    cost: float
    stock: int
    lead_hours: int
    ships_from: Optional[str] = None


@dataclass
class CompetitorItem:
    channel: str  # e.g., amazon|ebay|walmart
    price: float
    seller: Optional[str] = None
    asin: Optional[str] = None


@dataclass
class ProductIngestItem:
    sku: str
    asin: Optional[str]
    title: str
    brand: Optional[str]
    image: Optional[str]
    supplier: SupplierOfferItem
    competitor: Optional[CompetitorItem] = None


class SupplierAdapter:
    """Interface for supplier adapters."""

    name: str

    def fetch_products(self, limit: int = 10) -> List[ProductIngestItem]:  # pragma: no cover
        raise NotImplementedError
