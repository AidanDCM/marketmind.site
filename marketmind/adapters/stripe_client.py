"""Slice 16: Live Stripe Payment Links integration.

StripeClient wraps three sequential Stripe API calls required to create a
Payment Link from a raw price:
  1. POST /v1/products  — creates the product record
  2. POST /v1/prices    — attaches the price to the product
  3. POST /v1/payment_links — creates the shareable link

Safety gates (enforced before any HTTP call):
  - The ApprovalRecord must have risk_level=HIGH and status=APPROVED.
  - The PaymentLinkPayload must have dry_run=False.
  - unit_amount_cents must be > 0.
  - The API key is NEVER logged, printed, or included in responses.

Retries: up to 3 attempts on 5xx errors with 1-second exponential backoff
         (via tenacity). Network errors and 4xx are not retried.
Timeout: 10 seconds per request.

In test/dry-run mode, pass dry_run=True (the default) to get back a
simulated response without hitting the API.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from ..schemas import ApprovalRecord, ApprovalStatus, PaymentLinkPayload, RiskLevel

_STRIPE_BASE = "https://api.stripe.com/v1"
_TIMEOUT = 10.0
log = logging.getLogger(__name__)


def _is_server_error(exc: BaseException) -> bool:
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500


class StripeClient:
    """Thin Stripe REST client. Instantiate with a restricted API key."""

    def __init__(self, api_key: str) -> None:
        if not api_key.strip():
            raise ValueError("api_key is required")
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    @retry(
        retry=retry_if_exception(_is_server_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{_STRIPE_BASE}{path}"
        log.debug("stripe POST", extra={"path": path})
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(url, headers=self._headers(), data=data)
        resp.raise_for_status()
        return resp.json()

    def create_payment_link(
        self,
        payload: PaymentLinkPayload,
        approval: ApprovalRecord,
    ) -> dict[str, Any]:
        """Create a Stripe Payment Link from an approved PaymentLinkPayload.

        Returns the Stripe API response dict on success.
        Raises ValueError if the approval gate is not met.
        Raises ValueError if unit_amount_cents <= 0.
        Never logs the API key.
        """
        _assert_approved(approval, "create_payment_link")

        if payload.dry_run:
            raise ValueError(
                "PaymentLinkPayload.dry_run is True. "
                "Set dry_run=False explicitly to call the live Stripe API."
            )
        if payload.unit_amount_cents <= 0:
            raise ValueError("unit_amount_cents must be > 0 to create a Payment Link.")

        log.info(
            "creating Stripe Payment Link",
            extra={
                "product_name": payload.product_name,
                "approval_id": approval.approval_id,
                "amount_cents": payload.unit_amount_cents,
            },
        )

        # 1. Create product
        product = self._post("/products", {"name": payload.product_name})
        product_id = product["id"]

        # 2. Create price
        price = self._post(
            "/prices",
            {
                "product": product_id,
                "unit_amount": str(payload.unit_amount_cents),
                "currency": payload.currency,
            },
        )
        price_id = price["id"]

        # 3. Create payment link
        link_data: dict[str, Any] = {
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": "1",
        }
        for k, v in payload.metadata.items():
            link_data[f"metadata[{k}]"] = v

        link = self._post("/payment_links", link_data)

        log.info(
            "Stripe Payment Link created",
            extra={"payment_link_id": link.get("id"), "approval_id": approval.approval_id},
        )
        return link


# ---------------------------------------------------------------------------
# Dry-run simulation (no HTTP calls; for testing approval-gate logic)
# ---------------------------------------------------------------------------


def simulate_create_payment_link(
    payload: PaymentLinkPayload,
    approval: ApprovalRecord,
) -> dict[str, Any]:
    """Return a fake Stripe-shaped response without hitting the API.

    The approval gate is still enforced — this is for integration testing
    the gate logic, not for bypassing it.
    """
    _assert_approved(approval, "simulate_create_payment_link")
    return {
        "id": f"plink_simulated_{approval.approval_id}",
        "object": "payment_link",
        "active": True,
        "url": f"https://buy.stripe.com/simulated_{payload.product_name[:8]}",
        "metadata": dict(payload.metadata),
        "_dry_run": True,
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
