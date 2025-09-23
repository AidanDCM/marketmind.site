from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import httpx

from .config import get_settings

LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
SPAPI_BASE = {
    "na": "https://sellingpartnerapi-na.amazon.com",
    "eu": "https://sellingpartnerapi-eu.amazon.com",
    "fe": "https://sellingpartnerapi-fe.amazon.com",
}


class SpapiError(Exception):
    """Generic SP-API client error."""

    pass


class SpapiClient:
    """Lightweight SP-API client using typed settings with legacy env fallbacks.

    Prefers values from `packages.shared.config.AppSettings.amazon` and gracefully
    falls back to legacy environment variable names if needed.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        region: Optional[str] = None,
    ) -> None:
        settings = get_settings()

        # Typed settings
        typed_client_id = getattr(settings.amazon, "client_id", "")
        typed_client_secret = getattr(settings.amazon, "client_secret", "")
        typed_refresh_token = getattr(settings.amazon, "refresh_token", "")
        typed_region = getattr(settings.amazon, "region", "NA")

        # Legacy env fallbacks (support both SP-API and SP prefixes)
        legacy_client_id = (
            os.getenv("AMAZON_SP_API_CLIENT_ID")
            or os.getenv("AMAZON_SP_CLIENT_ID")
            or ""
        )
        legacy_client_secret = (
            os.getenv("AMAZON_SP_API_CLIENT_SECRET")
            or os.getenv("AMAZON_SP_CLIENT_SECRET")
            or ""
        )
        legacy_refresh_token = (
            os.getenv("AMAZON_SP_API_REFRESH_TOKEN")
            or os.getenv("AMAZON_SP_REFRESH_TOKEN")
            or ""
        )
        legacy_region = (
            os.getenv("AMAZON_SP_API_REGION")
            or os.getenv("AMAZON_SP_REGION")
            or typed_region
        )

        # Final values with explicit args taking precedence
        self.client_id = client_id or typed_client_id or legacy_client_id
        self.client_secret = client_secret or typed_client_secret or legacy_client_secret
        self.refresh_token = refresh_token or typed_refresh_token or legacy_refresh_token

        # Map SP-API region (NA/EU/FE) to client base keys (na/eu/fe)
        region_src = (region or legacy_region or typed_region or "NA").strip().upper()
        if region_src in {"US-EAST-1", "NA", "NORTHAMERICA", "USA"}:
            self.region = "na"
        elif region_src in {"EU-WEST-1", "EU", "EUROPE"}:
            self.region = "eu"
        elif region_src in {"AP-NORTHEAST-1", "FE", "FAR-EAST", "ASIA"}:
            self.region = "fe"
        else:
            # Default to NA
            self.region = "na"

        self._access_token: Optional[str] = None
        self._expiry_ts: float = 0.0
        # Marketplace ID can still come from env
        self.marketplace_id: Optional[str] = os.getenv("AMAZON_SP_MARKETPLACE_ID")

        if self.region not in SPAPI_BASE:
            raise SpapiError(f"Unsupported region: {self.region}")
        if not (self.client_id and self.client_secret and self.refresh_token):
            raise SpapiError(
                "Missing SP-API credentials; set AMAZON_SP_API_CLIENT_ID/SECRET/REFRESH_TOKEN"
            )

    def _ensure_token(self) -> None:
        now = time.time()
        if self._access_token and now < self._expiry_ts - 30:
            return
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                LWA_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
        if resp.status_code != 200:
            body = resp.text[:256] if hasattr(resp, "text") else ""
            raise SpapiError(f"LWA token error status={resp.status_code} body={body}")
        data = resp.json()
        self._access_token = data.get("access_token")
        expires_in = int(data.get("expires_in", 3600))
        self._expiry_ts = now + expires_in

    def _base_headers(self) -> Dict[str, str]:
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "x-amz-access-token": self._access_token or "",
            "Accept": "application/json",
        }

    def _base_url(self) -> str:
        return SPAPI_BASE[self.region]

    # Minimal endpoints (sandbox-compatible)
    def get_competitive_pricing(self, asins: List[str]) -> Dict[str, Any]:
        # SP-API Product Pricing API v0
        url = f"{self._base_url()}/products/pricing/v0/competitivePrice"
        params = {"Asins": ",".join(asins), "ItemType": "Asin"}
        if self.marketplace_id:
            params["MarketplaceId"] = self.marketplace_id
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=self._base_headers(), params=params)
        if resp.status_code != 200:
            body = resp.text[:256]
            raise SpapiError(f"pricing status={resp.status_code} body={body}")
        return resp.json()

    def update_listing_price(
        self,
        seller_id: str,
        sku: str,
        price: float,
        currency: str = "USD",
        marketplace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Best-effort update of listing price using Listings Items 2021-08-01 API.

        Notes:
        - This depends on the Listings Items API role being granted to your app.
        - Many accounts use Feeds API for price updates; adapt if needed for your org.
        - On failure, returns a structured JSON with error details.
        """
        if not seller_id:
            raise SpapiError("Missing AMAZON_SP_SELLER_ID (seller_id)")
        if not sku:
            raise SpapiError("SKU is required to update price (SKU often equals ASIN for simple flows)")
        mp = marketplace_id or self.marketplace_id
        if not mp:
            raise SpapiError("Missing AMAZON_SP_MARKETPLACE_ID for Listings Items call")

        # Listings Items 2021-08-01
        url = f"{self._base_url()}/listings/2021-08-01/items/{seller_id}/{sku}"
        params = {"marketplaceIds": mp}
        # Minimal JSON Patch payload to set price attribute; payload structure varies by productType.
        # This is a simplified patch and may require adjustment per your catalog/productType.
        patch_body = {
            "productType": "PRODUCT",
            "patches": [
                {
                    "op": "add",
                    "path": "/attributes/prices",
                    "value": [
                        {"currency": currency, "amount": float(price)}
                    ],
                }
            ],
        }
        with httpx.Client(timeout=20) as client:
            resp = client.patch(url, headers=self._base_headers(), params=params, json=patch_body)
        result: Dict[str, Any] = {"status": resp.status_code}
        try:
            body = resp.json()
        except Exception:  # pragma: no cover
            body = {"text": resp.text[:512] if hasattr(resp, "text") else ""}
        result["body"] = body
        if resp.status_code not in (200, 202):
            raise SpapiError(f"update_listing_price status={resp.status_code} body={str(body)[:256]}")
        return {"ok": True, "status": resp.status_code, "body": body}

    def get_catalog_item(self, asin: str, marketplace_id: Optional[str] = None) -> Dict[str, Any]:
        # Catalog Items 2022-04-01
        url = f"{self._base_url()}/catalog/2022-04-01/items/{asin}"
        params = {}
        # Prefer explicit marketplace_id when provided (e.g., health probes),
        # otherwise fall back to instance-level marketplace_id if available.
        mp = marketplace_id or self.marketplace_id
        if mp:
            params["marketplaceIds"] = mp
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=self._base_headers(), params=params or None)
        if resp.status_code != 200:
            body = resp.text[:256]
            raise SpapiError(f"catalog status={resp.status_code} body={body}")
        return resp.json()

    def get_marketplace_participations(self) -> Dict[str, Any]:
        """Fetch marketplace participations (Sellers API) to validate credentials.

        Minimal implementation for health probes.
        """
        url = f"{self._base_url()}/sellers/v1/marketplaceParticipations"
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=self._base_headers())
        if resp.status_code != 200:
            body = resp.text[:256]
            raise SpapiError(f"sellers status={resp.status_code} body={body}")
        return resp.json()

    @staticmethod
    def extract_best_price(pricing_payload: Dict[str, Any], asin: str) -> Optional[float]:
        # Very defensive parse of SP-API pricing structure
        try:
            for el in pricing_payload.get("payload", []):
                if el.get("ASIN") == asin:
                    for o in (
                        el.get("Product", {})
                        .get("CompetitivePricing", {})
                        .get("CompetitivePrices", [])
                    ):
                        price = o.get("Price", {}).get("ListingPrice", {}).get("Amount")
                        if price is not None:
                            return float(price)
        except Exception:
            return None
        return None

    @staticmethod
    def extract_buybox_flag(pricing_payload: Dict[str, Any], asin: str) -> Optional[bool]:
        try:
            for el in pricing_payload.get("payload", []):
                if el.get("ASIN") == asin:
                    bb = (
                        el.get("Product", {})
                        .get("CompetitivePricing", {})
                        .get("NumberOfOfferListings", [])
                    )
                    # Not a true buybox flag; placeholder using offers present
                    return bool(bb)
        except Exception:
            return None
        return None

    @staticmethod
    def extract_catalog_fields(catalog_payload: Dict[str, Any]) -> Dict[str, Optional[str]]:
        out: Dict[str, Optional[str]] = {"title": None, "brand": None, "category": None}
        try:
            attr = catalog_payload.get("attributes") or catalog_payload.get("payload", {}).get(
                "attributes"
            )
            if not attr:
                return out

            out["title"] = (
                (attr.get("item_name") or attr.get("title") or [None])[0]
                if isinstance(attr.get("item_name") or attr.get("title"), list)
                else (attr.get("item_name") or attr.get("title"))
            )
            out["brand"] = (
                (attr.get("brand") or [None])[0]
                if isinstance(attr.get("brand"), list)
                else attr.get("brand")
            )
            # category is often nested; omit for now
        except Exception:
            pass
        return out

# Backward-compat alias used by health probes
SPAPIClient = SpapiClient
