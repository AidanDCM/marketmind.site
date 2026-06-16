"""Slice 32: webhook ingestion endpoints."""

from __future__ import annotations

import json
import os

from fastapi import APIRouter, Header, HTTPException, Request

from ...db.import_store import save_import
from ...webhooks import (
    normalize_shopify_order_event,
    normalize_stripe_event,
    verify_shopify_signature,
    verify_stripe_signature,
)

router = APIRouter(tags=["webhooks"])


def _engine(request: Request):
    return request.app.state.engine


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
) -> dict:
    """Ingest a Stripe webhook event. Verifies the signature before processing."""
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=409, detail="STRIPE_WEBHOOK_SECRET not configured")
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    body = await request.body()
    try:
        verify_stripe_signature(body, stripe_signature, secret)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        event = json.loads(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    result = normalize_stripe_event(event)
    batch_id = save_import(_engine(request), result)
    return {"received": True, "batch_id": batch_id, "source": result.source}


@router.post("/shopify/orders")
async def shopify_order_webhook(
    request: Request,
    x_shopify_hmac_sha256: str = Header(None, alias="x-shopify-hmac-sha256"),
) -> dict:
    """Ingest a Shopify order webhook. Verifies the HMAC before processing."""
    secret = os.environ.get("SHOPIFY_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=409, detail="SHOPIFY_WEBHOOK_SECRET not configured")
    if not x_shopify_hmac_sha256:
        raise HTTPException(status_code=400, detail="Missing X-Shopify-Hmac-Sha256 header")

    body = await request.body()
    try:
        verify_shopify_signature(body, x_shopify_hmac_sha256, secret)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        payload = json.loads(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    result = normalize_shopify_order_event(payload)
    batch_id = save_import(_engine(request), result)
    return {"received": True, "batch_id": batch_id, "source": result.source}
