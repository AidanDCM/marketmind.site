"""Slice 32: inbound webhook handlers for Stripe and Shopify.

Both handlers:
  1. Verify the request signature (reject with 400 if invalid).
  2. Parse the event payload into the standard ImportResult shape.
  3. Persist the batch via save_import so it appears in import history.

Signature secrets are read from environment variables at call time — never
stored in the module or logged.

  STRIPE_WEBHOOK_SECRET   — Stripe signing secret (whsec_...)
  SHOPIFY_WEBHOOK_SECRET  — Shopify shared secret for HMAC-SHA256

Neither secret is required to run the API in development; the endpoints return
409 when the relevant secret is missing, matching the live-read pattern.
"""

from __future__ import annotations

import hashlib
import hmac
import time

from .schemas import ImportResult, ImportRow, ImportRowStatus

# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------

_STRIPE_TOLERANCE_SECONDS = 300  # 5-minute replay protection


def verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> None:
    """Raise ValueError if the Stripe-Signature header does not match.

    Implements Stripe's HMAC-SHA256 scheme:
    https://stripe.com/docs/webhooks/signatures
    """
    parts: dict[str, str] = {}
    for item in sig_header.split(","):
        if "=" in item:
            k, v = item.split("=", 1)
            parts[k.strip()] = v.strip()

    timestamp = parts.get("t")
    v1 = parts.get("v1")
    if not timestamp or not v1:
        raise ValueError("Stripe-Signature header is missing t= or v1=")

    # Replay protection
    age = abs(time.time() - int(timestamp))
    if age > _STRIPE_TOLERANCE_SECONDS:
        raise ValueError(f"Stripe webhook timestamp too old ({age:.0f}s)")

    signed_payload = f"{timestamp}.".encode() + payload
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, v1):
        raise ValueError("Stripe-Signature v1 mismatch")


def normalize_stripe_event(event: dict) -> ImportResult:
    """Turn a Stripe webhook event dict into an ImportResult."""
    event_type = event.get("type", "unknown")
    data_obj = event.get("data", {}).get("object", {})

    row_data: dict[str, str] = {
        "event_id": event.get("id", ""),
        "event_type": event_type,
        "object_id": data_obj.get("id", ""),
        "amount": str(data_obj.get("amount", "")),
        "currency": data_obj.get("currency", ""),
        "status": data_obj.get("status", ""),
        "created": str(data_obj.get("created", "")),
    }

    row = ImportRow(row_number=1, status=ImportRowStatus.OK, data=row_data)
    return ImportResult(
        source="stripe_webhook",
        total_rows=1,
        ok_rows=[row],
        review_rows=[],
    )


# ---------------------------------------------------------------------------
# Shopify
# ---------------------------------------------------------------------------


def verify_shopify_signature(payload: bytes, hmac_header: str, secret: str) -> None:
    """Raise ValueError if the X-Shopify-Hmac-Sha256 header does not match.

    Shopify uses Base64-encoded HMAC-SHA256 of the raw request body.
    """
    import base64

    expected = base64.b64encode(
        hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    ).decode()
    if not hmac.compare_digest(expected, hmac_header):
        raise ValueError("X-Shopify-Hmac-Sha256 mismatch")


def normalize_shopify_order_event(payload: dict) -> ImportResult:
    """Turn a Shopify order webhook payload into an ImportResult."""
    line_items = payload.get("line_items", [])
    product_name = line_items[0]["title"] if line_items else ""
    shipping_lines = payload.get("shipping_lines", [])
    shipping_cost = shipping_lines[0].get("price", "") if shipping_lines else ""
    financial_status = payload.get("financial_status", "")

    row_data: dict[str, str] = {
        "order_id": str(payload.get("id", "")),
        "date": payload.get("created_at", ""),
        "product_name": product_name,
        "sale_price": payload.get("total_price", ""),
        "financial_status": financial_status,
        "fulfillment_status": payload.get("fulfillment_status") or "",
        "shipping_cost": shipping_cost,
        "refunded": "true" if financial_status == "refunded" else "false",
    }

    row = ImportRow(row_number=1, status=ImportRowStatus.OK, data=row_data)
    return ImportResult(
        source="shopify_webhook_order",
        total_rows=1,
        ok_rows=[row],
        review_rows=[],
    )
