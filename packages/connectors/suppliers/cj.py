"""
CJ Dropshipping Supplier Adapter for MarketMind.

This module provides functionality to interact with the CJ Dropshipping API
for catalog synchronization, stock updates, and order placement.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ...shared.config import get_settings
from ...shared.db import get_session_factory
from ...shared.models_db import Product, SupplierOffer
from ...shared.sheets import get_ledger_writer
from ..http.backoff import BackoffConfig, retryable
from .base import (
    StockInfo,
    SupplierAuthError,
    SupplierError,
    SupplierRateLimitError,
    TrackingEvent,
)


class CJDropshippingAdapter:
    """Adapter for CJ Dropshipping API."""

    name = "cj"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.cj.api_key
        self.website_id = settings.cj.website_id
        self.base_url = settings.cj.base_url

        # Setup HTTP session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Rate limiting (CJ allows ~100 requests per minute)
        self._last_request_time: float = 0.0
        self._min_request_interval = 0.6  # 600ms between requests

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()

    def _headers(self) -> Dict[str, str]:
        """Get request headers with auth."""
        return {
            "CJ-Access-Token": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @retryable(exceptions=SupplierRateLimitError, max_retries=3, backoff=BackoffConfig(base=1.0))
    def _make_request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make authenticated request to CJ API with rate limiting."""
        self._rate_limit()

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {**self._headers(), **kwargs.pop("headers", {})}

        try:
            response = self.session.request(
                method=method, url=url, headers=headers, timeout=30, **kwargs
            )

            if response.status_code == 401:
                raise SupplierAuthError("CJ API authentication failed")
            elif response.status_code == 429:
                # First param is retry_after, so pass None explicitly then message
                raise SupplierRateLimitError(None, "CJ API rate limit exceeded")
            elif response.status_code >= 500:
                raise SupplierError(f"CJ API server error: {response.status_code}")
            elif response.status_code >= 400:
                raise SupplierError(
                    f"CJ API client error: {response.status_code} - {response.text}"
                )

            return cast(Dict[str, Any], response.json()) if response.content else {}

        except requests.exceptions.RequestException as e:
            raise SupplierError(f"CJ API request failed: {str(e)}") from e

    def health(self) -> Dict[str, Any]:
        """Check CJ API health with a small product list call."""
        if not self.api_key:
            return {"ok": False, "error": "api_key_missing"}

        try:
            start_time = time.time()
            # Test with a minimal product list call
            response = self._make_request("GET", "product/list", params={"pageSize": 1})
            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "ok": True,
                "latency_ms": latency_ms,
                "api_status": "connected",
                "products_available": response.get("data", {}).get("total", 0),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def sync_catalog_delta(self, *, org_id: str, brain_id: str) -> Dict[str, int]:
        """Sync CJ product catalog with idempotent upserts."""
        counts = {
            "products_created": 0,
            "products_updated": 0,
            "offers_created": 0,
            "offers_updated": 0,
            "skipped": 0,
        }

        try:
            Session = get_session_factory()
            db = Session()
            ledger = get_ledger_writer()

            # Fetch products from CJ API (paginated)
            page = 1
            page_size = 50

            while True:
                response = self._make_request(
                    "GET",
                    "product/list",
                    params={
                        "pageSize": page_size,
                        "pageNum": page,
                        "categoryId": "",  # All categories
                        "sortType": 1,  # Sort by update time
                    },
                )

                products_data = response.get("data", {}).get("list", [])
                if not products_data:
                    break

                for item in products_data:
                    try:
                        # Map CJ product to our canonical format
                        product_data = self._normalize_cj_product(item)
                        supplier_offer_data = self._normalize_cj_offer(item)

                        # Upsert product
                        product = db.query(Product).filter_by(sku=product_data["sku"]).first()

                        if product:
                            # Update existing product
                            for key, value in product_data.items():
                                if key != "sku":  # Don't update the unique key
                                    setattr(product, key, value)
                            counts["products_updated"] += 1
                        else:
                            # Create new product
                            product = Product(**product_data)
                            db.add(product)
                            counts["products_created"] += 1

                        db.flush()  # Get the product ID

                        # Upsert supplier offer
                        offer = (
                            db.query(SupplierOffer)
                            .filter_by(
                                supplier_name="cj", supplier_sku=supplier_offer_data["supplier_sku"]
                            )
                            .first()
                        )

                        supplier_offer_data["product_id"] = product.id

                        if offer:
                            # Update existing offer
                            for key, value in supplier_offer_data.items():
                                setattr(offer, key, value)
                            counts["offers_updated"] += 1
                        else:
                            # Create new offer
                            offer = SupplierOffer(**supplier_offer_data)
                            db.add(offer)
                            counts["offers_created"] += 1

                    except Exception as e:
                        print(f"Error processing CJ product {item.get('pid', 'unknown')}: {e}")
                        counts["skipped"] += 1
                        continue

                # Check if we have more pages
                total_pages = response.get("data", {}).get("pageTotal", 1)
                if page >= total_pages:
                    break
                page += 1

                # Rate limiting between pages
                time.sleep(0.5)

            db.commit()

            # Write summary to ledger
            ledger.client.append_rows_idempotent(
                "Supplier Sync Log",
                [
                    "timestamp",
                    "supplier",
                    "products_created",
                    "products_updated",
                    "offers_created",
                    "offers_updated",
                    "skipped",
                ],
                [
                    [
                        datetime.utcnow().isoformat(),
                        "cj",
                        counts["products_created"],
                        counts["products_updated"],
                        counts["offers_created"],
                        counts["offers_updated"],
                        counts["skipped"],
                    ]
                ],
            )

            return counts

        except Exception as e:
            if "db" in locals():
                db.rollback()
            raise SupplierError(f"CJ catalog sync failed: {str(e)}") from e
        finally:
            if "db" in locals():
                db.close()

    def _normalize_cj_product(self, cj_item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize CJ product data to our canonical format."""
        return {
            "sku": f"CJ-{cj_item.get('pid', '')}",
            "asin": None,  # CJ doesn't provide ASIN
            "title": cj_item.get("productName", ""),
            "brand": cj_item.get("productBrand", ""),
            "images": {
                "main": cj_item.get("productImage", ""),
                "additional": cj_item.get("productImages", []),
            },
        }

    def _normalize_cj_offer(self, cj_item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize CJ offer data to our canonical format."""
        # Convert price to cents
        price_usd = float(cj_item.get("sellPrice", 0))
        cost_cents = int(price_usd * 100)

        return {
            "supplier_name": "cj",
            "supplier_sku": str(cj_item.get("pid", "")),
            "cost": cost_cents / 100.0,  # Store as float for compatibility
            "stock_qty": int(cj_item.get("stockQty", 0)),
            "lead_time_hours": int(cj_item.get("processingTime", 3)) * 24,  # Convert days to hours
            "ships_from": cj_item.get("sourceCountry", "CN"),
            "active": cj_item.get("productStatus", 1) == 1,
            "meta": {
                "cj_pid": cj_item.get("pid"),
                "category_id": cj_item.get("categoryId"),
                "weight": cj_item.get("productWeight"),
                "dimensions": cj_item.get("productSize"),
                "last_sync": datetime.utcnow().isoformat(),
            },
        }

    def get_stock(self, supplier_sku: str, *, org_id: str, brain_id: str) -> StockInfo:
        """Get current stock info for a CJ product."""
        try:
            response = self._make_request("GET", "product/query", params={"pid": supplier_sku})

            product_data = response.get("data", {})
            if not product_data:
                raise SupplierError(f"CJ product not found: {supplier_sku}")

            return {
                "stock": int(product_data.get("stockQty", 0)),
                "lead_time_days": int(product_data.get("processingTime", 3)),
                "updated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise SupplierError(f"Failed to get CJ stock for {supplier_sku}: {str(e)}") from e

    def place_order(self, po: Dict[str, Any], *, org_id: str, brain_id: str) -> Dict[str, Any]:
        """Place order with CJ Dropshipping."""
        try:
            # Map our PO format to CJ's expected format
            cj_order = {
                "products": [],
                "shippingAddress": po.get("shipping_address", {}),
                "remark": po.get("notes", ""),
            }

            for item in po.get("items", []):
                cj_order["products"].append(
                    {
                        "pid": item["supplier_sku"],
                        "qty": item["quantity"],
                        "vid": item.get("variant_id", ""),
                    }
                )

            response = self._make_request("POST", "shopping/order/createOrder", json=cj_order)

            order_data = response.get("data", {})
            cj_order_id = order_data.get("orderId", "")

            # Write to supplier PO ledger
            ledger = get_ledger_writer()
            ledger.write_supplier_po(
                {
                    "supplier": "cj",
                    "supplier_sku": ",".join(
                        [item["supplier_sku"] for item in po.get("items", [])]
                    ),
                    "order_id": po.get("order_id", ""),
                    "cost": sum([item.get("cost", 0) for item in po.get("items", [])]),
                    "lead_time": po.get("lead_time_days", 3),
                    "status": "placed",
                }
            )

            return {
                "supplier_po_ref": cj_order_id,
                "status": "received",
                "estimated_ship_date": "",  # CJ doesn't provide this immediately
                "order_total": order_data.get("totalAmount", 0),
            }

        except Exception as e:
            raise SupplierError(f"Failed to place CJ order: {str(e)}") from e

    def get_tracking(
        self, supplier_po_ref: str, *, org_id: str, brain_id: str
    ) -> List[TrackingEvent]:
        """Get tracking events for CJ order."""
        try:
            response = self._make_request(
                "GET", "shopping/order/getOrderDetail", params={"orderId": supplier_po_ref}
            )

            order_data = response.get("data", {})
            tracking_events: List[TrackingEvent] = []

            # Parse CJ tracking data
            if order_data.get("trackingNumber"):
                tracking_events.append(
                    {
                        "event_time": order_data.get("shippedTime", datetime.utcnow().isoformat()),
                        "status": "shipped",
                        "location": order_data.get("sourceCountry", ""),
                        "description": f"Package shipped with tracking {order_data.get('trackingNumber')}",
                        "tracking_number": order_data.get("trackingNumber", ""),
                    }
                )

            return tracking_events

        except Exception as e:
            raise SupplierError(f"Failed to get CJ tracking for {supplier_po_ref}: {str(e)}") from e


# Create global instance
_cj_adapter: Optional[CJDropshippingAdapter] = None


def get_cj_adapter() -> CJDropshippingAdapter:
    global _cj_adapter
    if _cj_adapter is None:
        _cj_adapter = CJDropshippingAdapter()
    return _cj_adapter
