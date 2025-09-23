from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from .base import CompetitorItem, ProductIngestItem, SupplierAdapter, SupplierOfferItem

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore


class CJAdapter(SupplierAdapter):
    name = "cj"

    def __init__(self) -> None:
        self.api_key = os.getenv("CJ_API_KEY")
        # Base URL per CJ docs; adjust if needed. We'll keep endpoints flexible.
        self.base = os.getenv("CJ_API_BASE", "https://developers.cjdropshipping.com/api2")
        # Optional page size tuning
        self.page_size = int(os.getenv("CJ_PAGE_SIZE", "50"))

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise RuntimeError("CJ_API_KEY not set")
        return {
            "Content-Type": "application/json",
            "CJ-Access-Token": self.api_key,
        }

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if requests is None:
            raise RuntimeError("Python 'requests' not available for CJ adapter")
        url = f"{self.base}{path}"
        r = requests.get(url, headers=self._headers(), params=params or {}, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"CJ GET {path} status={r.status_code} body={r.text[:256]}")
        return r.json()

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if requests is None:
            raise RuntimeError("Python 'requests' not available for CJ adapter")
        url = f"{self.base}{path}"
        r = requests.post(url, headers=self._headers(), json=payload, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"CJ POST {path} status={r.status_code} body={r.text[:256]}")
        return r.json()

    def _normalize_item(self, it: Dict[str, Any]) -> Optional[ProductIngestItem]:
        # CJ product list typical fields (approximate; handle defensively)
        sku = str(it.get("sku")) if it.get("sku") else it.get("id") or it.get("productSku")
        title = it.get("productName") or it.get("name") or sku
        brand = it.get("brand")
        image = it.get("productImage") or it.get("imgUrl") or it.get("image")
        # Supplier fields
        supplier_sku = sku or str(it.get("id"))
        cost = float(it.get("sellPrice") or it.get("price") or 0.0)
        stock = int(it.get("stock") or it.get("inventory") or 0)
        lead_hours = int(it.get("leadTime") or 48)
        ships_from = it.get("warehouse") or it.get("shipsFrom") or None
        if not supplier_sku:
            return None
        supplier = SupplierOfferItem(
            supplier_name=self.name,
            supplier_sku=str(supplier_sku),
            cost=cost,
            stock=stock,
            lead_hours=lead_hours,
            ships_from=ships_from,
        )
        return ProductIngestItem(
            sku=str(supplier_sku),
            asin=None,
            title=str(title),
            brand=str(brand) if brand else None,
            image=str(image) if image else None,
            supplier=supplier,
            competitor=None,
        )

    def _fetch_page(self, page: int, size: int) -> List[ProductIngestItem]:
        # Some CJ product list endpoints use POST with pagination body
        # We'll try POST /product/list as primary; fall back to GET /product/list if POST fails
        payload = {"pageNum": page, "pageSize": size}
        items: List[ProductIngestItem] = []
        data: Dict[str, Any] = {}
        try:
            data = self._post("/product/list", payload)
        except Exception:
            # fallback to GET
            data = self._get("/product/list", params={"pageNum": page, "pageSize": size})
        # CJ often wraps data in { data: { list: [...] } } or { result: [...] }
        raw_list = (
            (data.get("data") or {}).get("list") or data.get("result") or data.get("data") or []
        )
        if isinstance(raw_list, dict):
            raw_list = raw_list.get("list", [])
        for raw in raw_list or []:
            try:
                ni = self._normalize_item(raw)
                if ni:
                    items.append(ni)
            except Exception:
                # skip malformed item
                continue
        return items

    def fetch_products(self, limit: int = 10) -> List[ProductIngestItem]:
        # If creds or HTTP missing, keep legacy stub behavior to avoid breaking local dev
        if not self.api_key or requests is None:
            # Legacy deterministic stub
            items: List[ProductIngestItem] = []
            items.append(
                ProductIngestItem(
                    sku="CJ-SANDBOX-001",
                    asin=None,
                    title="CJ Sandbox Pet Toy",
                    brand="CJ",
                    image="https://picsum.photos/seed/cj/600/600",
                    supplier=SupplierOfferItem(
                        supplier_name=self.name,
                        supplier_sku="CJ-XYZ-001",
                        cost=7.75,
                        stock=200,
                        lead_hours=36,
                        ships_from="US-CA",
                    ),
                    competitor=CompetitorItem(
                        channel="amazon",
                        price=18.49,
                        seller="CJSandboxSeller",
                        asin=None,
                    ),
                )
            )
            return items[: max(1, min(limit, len(items)))]

        out: List[ProductIngestItem] = []
        page = 1
        size = max(1, min(self.page_size, 100))
        target = max(1, limit)
        while len(out) < target:
            page_items = self._fetch_page(page, size)
            if not page_items:
                break
            for it in page_items:
                out.append(it)
                if len(out) >= target:
                    break
            page += 1
        return out[:target]


# Note: The CJAdapter above provides both real API-backed behavior when
# credentials and requests are available, and a deterministic sandbox stub
# when they are not, so a second stub class is unnecessary.
