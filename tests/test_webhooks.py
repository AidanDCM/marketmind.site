"""Slice 32: webhook handler tests."""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

import pytest

from marketmind.webhooks import (
    normalize_shopify_order_event,
    normalize_stripe_event,
    verify_shopify_signature,
    verify_stripe_signature,
)

# ---------------------------------------------------------------------------
# Stripe signature verification
# ---------------------------------------------------------------------------

def _stripe_sig(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    ts = timestamp if timestamp is not None else int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def test_stripe_valid_signature():
    payload = b'{"id":"evt_1","type":"charge.succeeded"}'
    secret = "whsec_test"
    sig = _stripe_sig(payload, secret)
    verify_stripe_signature(payload, sig, secret)  # no exception


def test_stripe_bad_signature_raises():
    payload = b'{"id":"evt_1"}'
    sig = _stripe_sig(payload, "whsec_test")
    with pytest.raises(ValueError, match="mismatch"):
        verify_stripe_signature(payload, sig, "whsec_wrong")


def test_stripe_replayed_timestamp_raises():
    payload = b'{"id":"evt_1"}'
    old_ts = int(time.time()) - 400  # > 300s tolerance
    sig = _stripe_sig(payload, "whsec_test", timestamp=old_ts)
    with pytest.raises(ValueError, match="too old"):
        verify_stripe_signature(payload, sig, "whsec_test")


def test_stripe_missing_fields_raises():
    with pytest.raises(ValueError, match="missing"):
        verify_stripe_signature(b"x", "v1=abc", "secret")


# ---------------------------------------------------------------------------
# Stripe normalization
# ---------------------------------------------------------------------------

def test_normalize_stripe_event():
    event = {
        "id": "evt_abc",
        "type": "charge.succeeded",
        "data": {
            "object": {
                "id": "ch_1",
                "amount": 5900,
                "currency": "usd",
                "status": "succeeded",
                "created": 1_700_000_000,
            }
        },
    }
    result = normalize_stripe_event(event)
    assert result.source == "stripe_webhook"
    assert result.total_rows == 1
    row = result.ok_rows[0].data
    assert row["event_type"] == "charge.succeeded"
    assert row["object_id"] == "ch_1"
    assert row["amount"] == "5900"


# ---------------------------------------------------------------------------
# Shopify HMAC verification
# ---------------------------------------------------------------------------

def _shopify_sig(payload: bytes, secret: str) -> str:
    return base64.b64encode(
        hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    ).decode()


def test_shopify_valid_signature():
    payload = b'{"id":111}'
    secret = "shpss_test"
    sig = _shopify_sig(payload, secret)
    verify_shopify_signature(payload, sig, secret)  # no exception


def test_shopify_bad_signature_raises():
    payload = b'{"id":111}'
    sig = _shopify_sig(payload, "shpss_test")
    with pytest.raises(ValueError, match="mismatch"):
        verify_shopify_signature(payload, sig, "shpss_wrong")


# ---------------------------------------------------------------------------
# Shopify order normalization
# ---------------------------------------------------------------------------

def test_normalize_shopify_order_event():
    payload = {
        "id": 112,
        "created_at": "2026-06-16T10:00:00Z",
        "total_price": "59.00",
        "financial_status": "paid",
        "fulfillment_status": "fulfilled",
        "line_items": [{"title": "Interior Kit"}],
        "shipping_lines": [{"price": "4.50"}],
    }
    result = normalize_shopify_order_event(payload)
    assert result.source == "shopify_webhook_order"
    row = result.ok_rows[0].data
    assert row["order_id"] == "112"
    assert row["product_name"] == "Interior Kit"
    assert row["shipping_cost"] == "4.50"
    assert row["refunded"] == "false"


def test_normalize_shopify_order_refunded():
    payload = {
        "id": 113,
        "created_at": "2026-06-16T11:00:00Z",
        "total_price": "0.00",
        "financial_status": "refunded",
        "fulfillment_status": None,
        "line_items": [],
        "shipping_lines": [],
    }
    result = normalize_shopify_order_event(payload)
    row = result.ok_rows[0].data
    assert row["refunded"] == "true"
    assert row["product_name"] == ""
    assert row["shipping_cost"] == ""
