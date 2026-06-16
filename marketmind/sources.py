"""Slice 27: read-only live data sources (Stripe + Shopify).

Pulls real data from Stripe and Shopify and normalizes it into the same
``ImportResult`` / ``ImportRow`` shape the CSV importers produce — so live reads
and CSV imports are interchangeable for everything downstream (reports, runner).

Safety:
  - **Read-only.** GET requests only. No writes, no money, no approvals needed.
  - Credentials come from the constructor or the environment; never logged.
  - Missing credentials raise at construction (``from_env``) — callers decide.
  - 5xx is retried (3 attempts, backoff); 10s/30s timeouts mirror the writers.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from .logging_config import get_logger
from .schemas import ImportResult, ImportRow, ImportRowStatus

log = get_logger(__name__)

_STRIPE_BASE = "https://api.stripe.com/v1"
_STRIPE_TIMEOUT = 10.0
_SHOPIFY_TIMEOUT = 30.0


def _is_server_error(exc: BaseException) -> bool:
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500


def _ok_rows(source: str, rows: list[dict[str, Any]]) -> ImportResult:
    result = ImportResult(source=source, total_rows=len(rows))
    for i, data in enumerate(rows, start=1):
        result.ok_rows.append(
            ImportRow(row_number=i, status=ImportRowStatus.OK, data=data)
        )
    return result


def _iso_from_unix(ts: int | float | None) -> str:
    if not ts:
        return ""
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Stripe (read-only)
# ---------------------------------------------------------------------------


class StripeReader:
    """Read-only Stripe client. Fetches charges and normalizes them to orders."""

    def __init__(self, api_key: str) -> None:
        if not api_key.strip():
            raise ValueError("api_key is required")
        self._api_key = api_key

    @classmethod
    def from_env(cls) -> StripeReader:
        key = os.environ.get("STRIPE_API_KEY", "")
        if not key.strip():
            raise ValueError("STRIPE_API_KEY is not set in the environment.")
        return cls(key)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    @retry(
        retry=retry_if_exception(_is_server_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{_STRIPE_BASE}{path}"
        log.debug("stripe GET", extra={"path": path})
        with httpx.Client(timeout=_STRIPE_TIMEOUT) as client:
            resp = client.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    def fetch_orders(self, limit: int = 100) -> ImportResult:
        """Fetch recent Stripe charges as normalized order rows."""
        payload = self._get("/charges", {"limit": limit})
        rows = [self._normalize_charge(c) for c in payload.get("data", [])]
        log.info("stripe orders fetched", extra={"count": len(rows)})
        return _ok_rows("stripe_charges", rows)

    @staticmethod
    def _normalize_charge(charge: dict[str, Any]) -> dict[str, str]:
        metadata = charge.get("metadata") or {}
        product_name = metadata.get("product_name") or charge.get("description") or ""
        amount = charge.get("amount", 0)  # cents
        return {
            "order_id": str(charge.get("id", "")),
            "date": _iso_from_unix(charge.get("created")),
            "product_name": str(product_name),
            "sale_price": f"{amount / 100:.2f}",
            "status": str(charge.get("status", "")),
            "refunded": "true" if charge.get("refunded") else "false",
            "shipping_cost": "",
        }


# ---------------------------------------------------------------------------
# Shopify (read-only)
# ---------------------------------------------------------------------------


class ShopifyReader:
    """Read-only Shopify Admin client. Fetches orders and products."""

    def __init__(self, store_domain: str, access_token: str) -> None:
        if not store_domain.strip():
            raise ValueError("store_domain is required")
        if not access_token.strip():
            raise ValueError("access_token is required")
        self._store_domain = store_domain.rstrip("/")
        self._access_token = access_token
        self._api_version = os.environ.get("SHOPIFY_API_VERSION", "2025-07")

    @classmethod
    def from_env(cls) -> ShopifyReader:
        domain = os.environ.get("SHOPIFY_STORE_DOMAIN", "")
        token = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
        if not domain.strip() or not token.strip():
            raise ValueError(
                "SHOPIFY_STORE_DOMAIN and SHOPIFY_ACCESS_TOKEN must be set."
            )
        return cls(domain, token)

    def _base_url(self) -> str:
        return f"https://{self._store_domain}/admin/api/{self._api_version}"

    def _headers(self) -> dict[str, str]:
        return {"X-Shopify-Access-Token": self._access_token}

    @retry(
        retry=retry_if_exception(_is_server_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url()}{path}"
        log.debug("shopify GET", extra={"path": path})
        with httpx.Client(timeout=_SHOPIFY_TIMEOUT) as client:
            resp = client.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    def fetch_orders(self, limit: int = 50) -> ImportResult:
        """Fetch recent Shopify orders as normalized order rows."""
        payload = self._get("/orders.json", {"limit": limit, "status": "any"})
        rows = [self._normalize_order(o) for o in payload.get("orders", [])]
        log.info("shopify orders fetched", extra={"count": len(rows)})
        return _ok_rows("shopify_orders", rows)

    def fetch_products(self, limit: int = 50) -> ImportResult:
        """Fetch products as normalized product rows."""
        payload = self._get("/products.json", {"limit": limit})
        rows = [self._normalize_product(p) for p in payload.get("products", [])]
        log.info("shopify products fetched", extra={"count": len(rows)})
        return _ok_rows("shopify_products", rows)

    @staticmethod
    def _normalize_order(order: dict[str, Any]) -> dict[str, str]:
        line_items = order.get("line_items") or []
        product_name = line_items[0].get("title", "") if line_items else ""
        financial = str(order.get("financial_status", ""))
        return {
            "order_id": str(order.get("id", "")),
            "date": str(order.get("created_at", "")),
            "product_name": str(product_name),
            "sale_price": str(order.get("total_price", "")),
            "status": str(order.get("fulfillment_status") or ""),
            "refunded": "true" if financial == "refunded" else "false",
            "shipping_cost": _shopify_shipping(order),
        }

    @staticmethod
    def _normalize_product(product: dict[str, Any]) -> dict[str, str]:
        variants = product.get("variants") or []
        price = variants[0].get("price", "") if variants else ""
        return {
            "product_name": str(product.get("title", "")),
            "sale_price": str(price),
            "product_cost": "",
            "shipping_cost": "",
            "niche": str(product.get("product_type", "")),
            "notes": str(product.get("status", "")),
        }


def _shopify_shipping(order: dict[str, Any]) -> str:
    lines = order.get("shipping_lines") or []
    try:
        total = sum(float(line.get("price", 0)) for line in lines)
    except (TypeError, ValueError):
        return ""
    return f"{total:.2f}" if lines else ""
