"""Slice 7: CSV import layer.

Adapts the CsvSourceAdapter pattern from Parts & Pieces
(AidanDCM/Parts-and-Pieces/parts/python/source_adapters/csv_source_adapter.py).
Inline adaptation — three concrete importers for the CSV shapes MarketMind
Autopilot currently needs: products, ad reports, orders.

Bad rows are flagged for review, never silently dropped and never raise.
Accepts in-memory text (io.StringIO-compatible) so tests need no temp files.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from .schemas import ImportResult, ImportRow, ImportRowStatus

# ---------------------------------------------------------------------------
# Internal helpers — adapted from CsvSourceAdapter pattern
# ---------------------------------------------------------------------------


def _norm_key(key: str) -> str:
    return key.strip().lower().replace("_", " ").replace("-", " ")


def _normalize_row(row: dict[str, Any]) -> dict[str, str]:
    return {_norm_key(k): str(v).strip() for k, v in row.items()}


def _pick(norm: dict[str, str], *aliases: str) -> str:
    for alias in aliases:
        value = norm.get(_norm_key(alias), "")
        if value:
            return value
    return ""


def _read_csv(text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def _validate_numerics(data: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    notes: list[str] = []
    for field in fields:
        val = data.get(field, "")
        if val:
            try:
                float(val)
            except ValueError:
                notes.append(f"{field} is not a valid number: {val!r}")
    return notes


# ---------------------------------------------------------------------------
# Product CSV importer
# ---------------------------------------------------------------------------

_PRODUCT_FIELDS: dict[str, tuple[str, ...]] = {
    "product_name": ("product_name", "name", "title", "product"),
    "sale_price": ("sale_price", "price", "sell_price", "selling_price"),
    "product_cost": ("product_cost", "cost", "cogs", "unit_cost"),
    "shipping_cost": ("shipping_cost", "shipping", "ship_cost"),
    "niche": ("niche", "category", "market"),
    "notes": ("notes", "comments", "description"),
}
_PRODUCT_REQUIRED = ("product_name",)
_PRODUCT_NUMERIC = ("sale_price", "product_cost", "shipping_cost")


def import_products_csv(text: str, source: str = "products") -> ImportResult:
    """Import a product candidates CSV.

    Required column: product_name (aliases: name, title, product).
    """
    raw_rows = _read_csv(text)
    result = ImportResult(source=source, total_rows=len(raw_rows))

    for i, raw in enumerate(raw_rows, start=1):
        norm = _normalize_row(raw)
        data: dict[str, Any] = {
            field: _pick(norm, *aliases) for field, aliases in _PRODUCT_FIELDS.items()
        }

        missing = [f for f in _PRODUCT_REQUIRED if not data.get(f)]
        if missing:
            result.review_rows.append(ImportRow(
                row_number=i,
                status=ImportRowStatus.REVIEW,
                data=data,
                notes=f"Missing required fields: {', '.join(missing)}",
            ))
            continue

        note_parts = _validate_numerics(data, _PRODUCT_NUMERIC)
        if note_parts:
            result.review_rows.append(ImportRow(
                row_number=i,
                status=ImportRowStatus.REVIEW,
                data=data,
                notes="; ".join(note_parts),
            ))
        else:
            result.ok_rows.append(ImportRow(row_number=i, status=ImportRowStatus.OK, data=data))

    return result


# ---------------------------------------------------------------------------
# Ad report CSV importer
# ---------------------------------------------------------------------------

_AD_FIELDS: dict[str, tuple[str, ...]] = {
    "campaign_name": ("campaign_name", "campaign", "ad_name", "ad name"),
    "date": ("date", "report_date", "day"),
    "impressions": ("impressions", "impr"),
    "clicks": ("clicks", "link_clicks", "link clicks"),
    "spend": ("spend", "cost", "amount_spent", "amount spent"),
    "purchases": ("purchases", "conversions", "orders", "results"),
    "revenue": ("revenue", "purchase_value", "conversion_value", "purchase value"),
}
_AD_REQUIRED = ("campaign_name",)
_AD_NUMERIC = ("impressions", "clicks", "spend", "purchases", "revenue")


def import_ad_report_csv(text: str, source: str = "ad_report") -> ImportResult:
    """Import a paid-ad performance CSV (e.g. Meta or TikTok export).

    Required column: campaign_name.
    """
    raw_rows = _read_csv(text)
    result = ImportResult(source=source, total_rows=len(raw_rows))

    for i, raw in enumerate(raw_rows, start=1):
        norm = _normalize_row(raw)
        data: dict[str, Any] = {
            field: _pick(norm, *aliases) for field, aliases in _AD_FIELDS.items()
        }

        missing = [f for f in _AD_REQUIRED if not data.get(f)]
        if missing:
            result.review_rows.append(ImportRow(
                row_number=i,
                status=ImportRowStatus.REVIEW,
                data=data,
                notes=f"Missing required fields: {', '.join(missing)}",
            ))
            continue

        note_parts = _validate_numerics(data, _AD_NUMERIC)
        if note_parts:
            result.review_rows.append(ImportRow(
                row_number=i,
                status=ImportRowStatus.REVIEW,
                data=data,
                notes="; ".join(note_parts),
            ))
        else:
            result.ok_rows.append(ImportRow(row_number=i, status=ImportRowStatus.OK, data=data))

    return result


# ---------------------------------------------------------------------------
# Order CSV importer
# ---------------------------------------------------------------------------

_ORDER_FIELDS: dict[str, tuple[str, ...]] = {
    "order_id": ("order_id", "order id", "id", "order_number", "order number"),
    "date": ("date", "order_date", "created_at", "created at"),
    "product_name": ("product_name", "product", "name", "item_name", "item name"),
    "sale_price": ("sale_price", "price", "total", "order_total", "order total"),
    "status": ("status", "fulfillment_status", "fulfillment status"),
    "refunded": ("refunded", "refund", "is_refunded", "is refunded"),
    "shipping_cost": ("shipping_cost", "shipping", "ship_cost", "ship cost"),
}
_ORDER_REQUIRED = ("order_id",)
_ORDER_NUMERIC = ("sale_price", "shipping_cost")


def import_orders_csv(text: str, source: str = "orders") -> ImportResult:
    """Import an orders CSV (e.g. Shopify or Stripe export).

    Required column: order_id.
    """
    raw_rows = _read_csv(text)
    result = ImportResult(source=source, total_rows=len(raw_rows))

    for i, raw in enumerate(raw_rows, start=1):
        norm = _normalize_row(raw)
        data: dict[str, Any] = {
            field: _pick(norm, *aliases) for field, aliases in _ORDER_FIELDS.items()
        }

        missing = [f for f in _ORDER_REQUIRED if not data.get(f)]
        if missing:
            result.review_rows.append(ImportRow(
                row_number=i,
                status=ImportRowStatus.REVIEW,
                data=data,
                notes=f"Missing required fields: {', '.join(missing)}",
            ))
            continue

        note_parts = _validate_numerics(data, _ORDER_NUMERIC)
        if note_parts:
            result.review_rows.append(ImportRow(
                row_number=i,
                status=ImportRowStatus.REVIEW,
                data=data,
                notes="; ".join(note_parts),
            ))
        else:
            result.ok_rows.append(ImportRow(row_number=i, status=ImportRowStatus.OK, data=data))

    return result
