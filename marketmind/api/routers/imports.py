"""Slice 29: import history endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...ad_summary import summarize_latest_ad_batch
from ...db.import_store import get_import, list_imports, save_import
from ...importers import import_ad_report_csv
from ...sources import ShopifyReader, StripeReader

router = APIRouter(tags=["imports"])


def _engine(request: Request):
    return request.app.state.engine


@router.post("/pull/stripe/orders")
def pull_and_save_stripe(request: Request, limit: int = 100) -> dict:
    """Pull Stripe charges, persist the batch, and return a summary."""
    try:
        reader = StripeReader.from_env()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    result = reader.fetch_orders(limit=limit)
    batch_id = save_import(_engine(request), result)
    return {"batch_id": batch_id, **result.to_dict()}


@router.post("/pull/shopify/orders")
def pull_and_save_shopify_orders(request: Request, limit: int = 50) -> dict:
    """Pull Shopify orders, persist the batch, and return a summary."""
    try:
        reader = ShopifyReader.from_env()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    result = reader.fetch_orders(limit=limit)
    batch_id = save_import(_engine(request), result)
    return {"batch_id": batch_id, **result.to_dict()}


@router.post("/pull/shopify/products")
def pull_and_save_shopify_products(request: Request, limit: int = 50) -> dict:
    """Pull Shopify products, persist the batch, and return a summary."""
    try:
        reader = ShopifyReader.from_env()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    result = reader.fetch_products(limit=limit)
    batch_id = save_import(_engine(request), result)
    return {"batch_id": batch_id, **result.to_dict()}


class AdCsvImportRequest(BaseModel):
    csv_text: str
    source: str = "ad_report_csv"


@router.post("/ads/csv")
def import_ad_csv_endpoint(request: Request, body: AdCsvImportRequest) -> dict:
    """Import a Meta/Google/TikTok ad performance CSV export and persist the batch."""
    if not body.csv_text.strip():
        raise HTTPException(status_code=422, detail="csv_text must not be empty")
    result = import_ad_report_csv(body.csv_text, source=body.source)
    batch_id = save_import(_engine(request), result)
    return {"batch_id": batch_id, **result.to_dict()}


@router.get("/ads/summary")
def ad_spend_summary_endpoint(request: Request) -> dict:
    """Return aggregated spend metrics from the latest ad import batch."""
    summary = summarize_latest_ad_batch(_engine(request))
    if summary is None:
        return {"has_data": False, "summary": None}
    return {"has_data": True, "summary": summary.to_dict()}


@router.get("")
def list_import_history(request: Request, source: str | None = None, limit: int = 50) -> list:
    """List recent import batches, newest first."""
    return list_imports(_engine(request), source=source, limit=limit)


@router.get("/{batch_id}")
def get_import_batch(request: Request, batch_id: int) -> dict:
    """Return a single import batch with all row data."""
    batch = get_import(_engine(request), batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch not found")
    return batch
