from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...sources import ShopifyReader, StripeReader

router = APIRouter(tags=["sources"])


@router.post("/stripe/orders")
def stripe_orders_endpoint(limit: int = 100) -> dict:
    """Pull recent Stripe charges as normalized order rows. Read-only."""
    try:
        reader = StripeReader.from_env()
    except ValueError as exc:
        # No credentials configured — safe-fail with a clear message.
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return reader.fetch_orders(limit=limit).to_dict()


@router.post("/shopify/orders")
def shopify_orders_endpoint(limit: int = 50) -> dict:
    """Pull recent Shopify orders as normalized order rows. Read-only."""
    try:
        reader = ShopifyReader.from_env()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return reader.fetch_orders(limit=limit).to_dict()


@router.post("/shopify/products")
def shopify_products_endpoint(limit: int = 50) -> dict:
    """Pull Shopify products as normalized product rows. Read-only."""
    try:
        reader = ShopifyReader.from_env()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return reader.fetch_products(limit=limit).to_dict()
