"""Slice 17: Live Shopify product draft integration.

ShopifyClient wraps the Shopify Admin REST API to create product drafts.
The product is always created with status='draft'. Publishing (setting
status='active') is a separate operation that also requires approval.

Safety gates (enforced before any HTTP call):
  - The ApprovalRecord must have risk_level=HIGH and status=APPROVED.
  - The ProductDraftPayload must have dry_run=False.
  - store_domain must not be empty.
  - The access token is NEVER logged, printed, or included in responses.

Retries: up to 3 attempts on 5xx with exponential backoff (tenacity).
Timeout: 30 seconds per request (Shopify can be slow).
API version: read from SHOPIFY_API_VERSION env var, defaults to 2025-07.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from ..schemas import ApprovalRecord, ApprovalStatus, ProductDraftPayload, RiskLevel

_TIMEOUT = 30.0
log = logging.getLogger(__name__)


def _is_server_error(exc: BaseException) -> bool:
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500


class ShopifyClient:
    """Thin Shopify Admin REST client."""

    def __init__(self, store_domain: str, access_token: str) -> None:
        if not store_domain.strip():
            raise ValueError("store_domain is required")
        if not access_token.strip():
            raise ValueError("access_token is required")
        self._store_domain = store_domain.rstrip("/")
        self._access_token = access_token
        self._api_version = os.environ.get("SHOPIFY_API_VERSION", "2025-07")

    def _base_url(self) -> str:
        return f"https://{self._store_domain}/admin/api/{self._api_version}"

    def _headers(self) -> dict[str, str]:
        return {
            "X-Shopify-Access-Token": self._access_token,
            "Content-Type": "application/json",
        }

    @retry(
        retry=retry_if_exception(_is_server_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url()}{path}"
        log.debug("shopify POST", extra={"path": path})
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(url, headers=self._headers(), json=body)
        resp.raise_for_status()
        return resp.json()

    def create_product_draft(
        self,
        payload: ProductDraftPayload,
        approval: ApprovalRecord,
    ) -> dict[str, Any]:
        """Create a Shopify product in draft status.

        Returns the Shopify API response dict on success.
        Raises ValueError if the approval gate is not met.
        Never logs the access token.
        """
        _assert_approved(approval, "create_product_draft")

        if payload.dry_run:
            raise ValueError(
                "ProductDraftPayload.dry_run is True. "
                "Set dry_run=False explicitly to call the live Shopify API."
            )

        log.info(
            "creating Shopify product draft",
            extra={
                "title": payload.title,
                "approval_id": approval.approval_id,
                "store": self._store_domain,
            },
        )

        product_body: dict[str, Any] = {
            "product": {
                "title": payload.title,
                "body_html": payload.body_html,
                "vendor": payload.vendor,
                "product_type": payload.product_type,
                "status": "draft",
                "tags": payload.tags,
                "variants": [v.to_dict() for v in payload.variants],
            }
        }

        result = self._post("/products.json", product_body)

        product_id = result.get("product", {}).get("id")
        log.info(
            "Shopify product draft created",
            extra={"product_id": product_id, "approval_id": approval.approval_id},
        )
        return result


# ---------------------------------------------------------------------------
# Dry-run simulation
# ---------------------------------------------------------------------------


def simulate_create_product_draft(
    payload: ProductDraftPayload,
    approval: ApprovalRecord,
) -> dict[str, Any]:
    """Return a fake Shopify-shaped response without hitting the API.

    The approval gate is still enforced.
    """
    _assert_approved(approval, "simulate_create_product_draft")
    return {
        "product": {
            "id": f"simulated_{approval.approval_id}",
            "title": payload.title,
            "status": "draft",
            "vendor": payload.vendor,
            "variants": [v.to_dict() for v in payload.variants],
            "_dry_run": True,
        }
    }


# ---------------------------------------------------------------------------
# Internal gate helper
# ---------------------------------------------------------------------------


def _assert_approved(approval: ApprovalRecord, operation: str) -> None:
    if approval.risk_level != RiskLevel.HIGH:
        raise ValueError(
            f"{operation} requires a HIGH-risk ApprovalRecord. "
            f"Got: {approval.risk_level.value!r}."
        )
    if approval.status != ApprovalStatus.APPROVED:
        raise ValueError(
            f"{operation} requires status=APPROVED. "
            f"Got: {approval.status.value!r}."
        )
