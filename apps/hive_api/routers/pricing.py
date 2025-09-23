from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc

from packages.shared.config import get_settings
from packages.shared.db import get_db
from packages.shared.models_db import (
    ChannelListing,
    PriceHistory,
    Product,
    PricingSimulation,
    SupplierOffer,
)
from packages.shared.spapi_client import SpapiClient, SpapiError
from packages.shared.pricing import Guardrails as PriceGuardrails, landed_cost
from packages.shared.guardrails import load_guardrails

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore

router = APIRouter()

# Optional Sentry breadcrumbs for pricing operations
try:  # pragma: no cover - optional dependency
    import sentry_sdk  # type: ignore
except Exception:  # pragma: no cover
    sentry_sdk = None  # type: ignore

def _sentry_breadcrumb(level: str, category: str, message: str, data: dict | None = None) -> None:
    if sentry_sdk is None:
        return
    try:  # pragma: no cover
        sentry_sdk.add_breadcrumb(
            type="default",
            category=category,
            message=message,
            level=level,
            data=data or {},
        )
    except Exception:
        pass


class SnapshotRequest(BaseModel):
    asins: List[str]


@router.post("/snapshot")
def pricing_snapshot(req: SnapshotRequest) -> Dict[str, Any]:
    if not req.asins:
        raise HTTPException(status_code=400, detail="asins is required")

    # Initialize SP-API client
    try:
        client = SpapiClient()
    except SpapiError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    # Simple rate-limit: one snapshot per 10 seconds (Redis if available)
    settings = get_settings()
    allowed = True
    reason = None
    key = "rate:pricing_snapshot"
    if redis and settings.REDIS_URL:
        try:
            r = redis.from_url(settings.REDIS_URL)
            allowed = bool(r.set(key, "1", nx=True, ex=10))
            if not allowed:
                reason = "rate_limited"
        except Exception:
            # fallback to memory
            pass
    if not redis or reason is None:
        # in-memory fallback using module global timestamp
        now = time.time()
        last = getattr(pricing_snapshot, "_last_ts", 0.0)
        if now - last < 10:
            allowed = False
            reason = "rate_limited"
        else:
            pricing_snapshot._last_ts = now
    if not allowed:
        _sentry_breadcrumb(
            level="warning",
            category="pricing.snapshot",
            message="Pricing snapshot rate limited",
            data={"reason": reason or "rate_limited", "asins": len(req.asins)},
        )
        raise HTTPException(status_code=429, detail=reason or "rate_limited")

    processed = 0
    errors: List[Dict[str, str]] = []
    # Chunk calls for pricing
    CHUNK = 10
    for i in range(0, len(req.asins), CHUNK):
        chunk = req.asins[i : i + CHUNK]
        try:
            pricing_payload = client.get_competitive_pricing(chunk)
        except Exception as e:
            errors.append({"scope": "pricing", "asins": ",".join(chunk), "error": str(e)})
            _sentry_breadcrumb(
                level="error",
                category="pricing.snapshot",
                message="Competitive pricing fetch failed",
                data={"asins": ",".join(chunk), "error": str(e)},
            )
            continue

        # For each ASIN, also get catalog details and write DB
        for asin in chunk:
            try:
                try:
                    cat = client.get_catalog_item(asin)
                except Exception:
                    cat = {}
                fields = client.extract_catalog_fields(cat)
                best_price = client.extract_best_price(pricing_payload, asin)
                # buybox flag placeholder
                _ = client.extract_buybox_flag(pricing_payload, asin)

                # Write DB
                for session in get_db():
                    # Upsert product (by asin); fallback sku=asin
                    existing = session.execute(
                        select(Product).where(Product.asin == asin)
                    ).scalar_one_or_none()
                    if existing is None:
                        p = Product(
                            sku=asin,
                            asin=asin,
                            title=fields.get("title") or asin,
                            brand=fields.get("brand"),
                        )
                        session.add(p)
                        session.flush()
                    else:
                        p = existing
                        # Update known fields
                        if fields.get("title"):
                            p.title = fields["title"]
                        if fields.get("brand"):
                            p.brand = fields["brand"]

                    # Ensure a draft channel listing exists for Amazon
                    cl = session.execute(
                        select(ChannelListing).where(
                            ChannelListing.product_id == p.id, ChannelListing.channel == "amazon"
                        )
                    ).scalar_one_or_none()
                    if cl is None:
                        cl = ChannelListing(
                            channel="amazon",
                            product_id=p.id,
                            listing_ref=asin,
                            status="draft",
                            price=None,
                        )
                        session.add(cl)

                    # Price history if we have a price
                    if best_price is not None:
                        session.add(
                            PriceHistory(
                                product_id=p.id,
                                channel="amazon",
                                price=float(best_price),
                                source="spapi",
                            )
                        )

                    session.commit()
                    break
                processed += 1
            except Exception as e:
                errors.append({"scope": "asin", "asin": asin, "error": str(e)})
                _sentry_breadcrumb(
                    level="error",
                    category="pricing.snapshot",
                    message="ASIN snapshot failed",
                    data={"asin": asin, "error": str(e)},
                )

    result = {"ok": True, "processed": processed, "errors": errors}
    _sentry_breadcrumb(
        level="info",
        category="pricing.snapshot",
        message="Pricing snapshot complete",
        data={"processed": processed, "errors": len(errors)},
    )
    return result


@router.get("/history")
def pricing_history(asin: str, limit: int = 30) -> Dict[str, Any]:
    if not asin:
        raise HTTPException(status_code=400, detail="asin is required")
    limit = max(1, min(200, limit))
    out: List[Dict[str, Any]] = []
    for session in get_db():
        p = session.execute(select(Product).where(Product.asin == asin)).scalar_one_or_none()
        if p is None:
            return {"asin": asin, "history": []}
        rows = (
            session.query(PriceHistory)
            .filter(PriceHistory.product_id == p.id)
            .order_by(PriceHistory.recorded_at.desc())
            .limit(limit)
            .all()
        )
        for r in rows:
            out.append(
                {
                    "channel": r.channel,
                    "price": r.price,
                    "source": r.source,
                    "recorded_at": r.recorded_at.isoformat(),
                }
            )
        break
    return {"asin": asin, "history": out}


class PushAmazonRequest(BaseModel):
    product_id: Optional[int] = None
    asin: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    currency: str = "USD"
    dry_run: bool = False


@router.post("/push/amazon")
def push_amazon_price(body: PushAmazonRequest) -> Dict[str, Any]:
    """Publish a price to Amazon via SP-API Listings Items.

    Resolution priority:
    - Identify product by product_id, else asin, else sku.
    - Price priority: explicit body.price; else latest approved PricingSimulation; else ChannelListing price; else last PriceHistory price.
    """
    # Resolve product
    prod: Optional[Product] = None
    with next(get_db()) as session:
        if body.product_id is not None:
            prod = session.execute(select(Product).where(Product.id == body.product_id)).scalar_one_or_none()
        elif body.asin:
            prod = session.execute(select(Product).where(Product.asin == body.asin)).scalar_one_or_none()
        elif body.sku:
            prod = session.execute(select(Product).where(Product.sku == body.sku)).scalar_one_or_none()
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")

        # Determine price
        price_val: Optional[float] = body.price
        # Initialize references used later for guardrails
        cl: Optional[ChannelListing] = None
        ph: Optional[PriceHistory] = None
        if price_val is None:
            sim = (
                session.query(PricingSimulation)
                .filter(PricingSimulation.product_id == prod.id, PricingSimulation.status == "approved")
                .order_by(desc(PricingSimulation.created_at))
                .first()
            )
            if sim and sim.proposed_price is not None:
                price_val = float(sim.proposed_price)
        if price_val is None:
            cl = (
                session.query(ChannelListing)
                .filter(ChannelListing.product_id == prod.id, ChannelListing.channel == "amazon")
                .first()
            )
            if cl and cl.price is not None:
                price_val = float(cl.price)
        if price_val is None:
            ph = (
                session.query(PriceHistory)
                .filter(PriceHistory.product_id == prod.id, PriceHistory.channel == "amazon")
                .order_by(PriceHistory.recorded_at.desc())
                .first()
            )
            if ph and ph.price is not None:
                price_val = float(ph.price)

        # Brand denylist (env: BRAND_DENYLIST=BrandA,BrandB)
        denylist = {b.strip().lower() for b in os.getenv("BRAND_DENYLIST", "").split(",") if b.strip()}
        if prod.brand and prod.brand.lower() in denylist:
            raise HTTPException(status_code=403, detail="brand_denied")

        # Enforce guardrails: min margin and max delta vs last price
        # Supplier cost: pick the lowest active supplier cost for prudence
        supplier_cost: Optional[float] = None
        off = (
            session.query(SupplierOffer)
            .filter(SupplierOffer.product_id == prod.id, SupplierOffer.active == True)
            .order_by(SupplierOffer.cost.asc())
            .first()
        )
        if off:
            supplier_cost = float(off.cost)
        # Build pricing guardrails, merging configured min margin where available
        cfg = load_guardrails()
        pguard = PriceGuardrails()
        # Override min_net_margin_pct from config if present
        try:
            pguard.min_net_margin_pct = float(getattr(cfg, "min_net_margin_pct", pguard.min_net_margin_pct))
        except Exception:
            pass
        # Compute margin at requested price (if cost known)
        if supplier_cost is not None and price_val is not None:
            lc = landed_cost(
                supplier_cost=supplier_cost,
                shipping_flat=pguard.est_shipping_flat if pguard.free_shipping_enabled else 0.0,
                platform_fee_pct=pguard.platform_fee_pct,
                return_reserve_pct=pguard.return_reserve_pct,
                target_price=price_val,
            )
            margin_pct = max(0.0, (price_val - lc) / price_val * 100.0) if price_val > 0 else 0.0
            if margin_pct < pguard.min_net_margin_pct:
                raise HTTPException(status_code=400, detail="below_min_margin")

        # Enforce max delta vs last price
        last_price: Optional[float] = None
        # Prefer current listing price if available
        if cl is None:
            cl = (
                session.query(ChannelListing)
                .filter(ChannelListing.product_id == prod.id, ChannelListing.channel == "amazon")
                .first()
            )
        if cl and cl.price is not None:
            last_price = float(cl.price)
        # Fallback to latest price history
        if last_price is None:
            if ph is None:
                ph = (
                    session.query(PriceHistory)
                    .filter(PriceHistory.product_id == prod.id, PriceHistory.channel == "amazon")
                    .order_by(PriceHistory.recorded_at.desc())
                    .first()
                )
            if ph and ph.price is not None:
                last_price = float(ph.price)
        if last_price and price_val:
            try:
                max_delta_pct = float(os.getenv("MAX_PRICE_DELTA_PCT", "20"))
            except Exception:
                max_delta_pct = 20.0
            if last_price > 0:
                delta_pct = abs(price_val - last_price) / last_price * 100.0
                if delta_pct > max_delta_pct:
                    raise HTTPException(status_code=400, detail="max_delta_exceeded")

    if price_val is None:
        raise HTTPException(status_code=400, detail="No price available (provide price or approve a proposal)")

    sku_to_use = (body.sku or (prod.sku if prod and prod.sku else prod.asin if prod else None))
    if not sku_to_use:
        raise HTTPException(status_code=400, detail="SKU/ASIN missing; set product.sku or provide sku in request")

    try:
        if body.dry_run:
            _sentry_breadcrumb(
                level="info",
                category="pricing.push",
                message="Amazon price push dry-run",
                data={"sku": sku_to_use, "price": price_val},
            )
            return {"ok": True, "dry_run": True, "sku": sku_to_use, "price": price_val}

        seller_id = os.getenv("AMAZON_SP_SELLER_ID", "")
        if not seller_id:
            raise HTTPException(status_code=503, detail="Missing AMAZON_SP_SELLER_ID")

        client = SpapiClient()
        result = client.update_listing_price(
            seller_id=seller_id,
            sku=sku_to_use,
            price=price_val,
            currency=body.currency,
        )
        # Persist to DB (best-effort)
        for session in get_db():
            p = session.execute(select(Product).where(Product.id == prod.id)).scalar_one()
            cl2 = (
                session.query(ChannelListing)
                .filter(ChannelListing.product_id == p.id, ChannelListing.channel == "amazon")
                .first()
            )
            if cl2 is None:
                cl2 = ChannelListing(
                    channel="amazon", product_id=p.id, listing_ref=p.asin or sku_to_use, status="active"
                )
                session.add(cl2)
            cl2.price = float(price_val)
            session.add(
                PriceHistory(
                    product_id=p.id,
                    channel="amazon",
                    price=float(price_val),
                    source="our_push",
                )
            )
            session.commit()
            break

        _sentry_breadcrumb(
            level="info",
            category="pricing.push",
            message="Amazon price push ok",
            data={"sku": sku_to_use, "price": price_val, "status": result.get("status")},
        )
        return {"ok": True, "sku": sku_to_use, "price": price_val, "result": result}
    except SpapiError as e:
        _sentry_breadcrumb(
            level="error",
            category="pricing.push",
            message="Amazon price push failed",
            data={"sku": sku_to_use, "price": price_val, "error": str(e)},
        )
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:  # pragma: no cover
        _sentry_breadcrumb(
            level="error",
            category="pricing.push",
            message="Amazon price push unexpected error",
            data={"sku": sku_to_use, "price": price_val, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="unexpected_error") from e


class PushAmazonBatchItem(BaseModel):
    product_id: Optional[int] = None
    asin: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None


class PushAmazonBatchRequest(BaseModel):
    items: List[PushAmazonBatchItem]
    dry_run: bool = False


@router.post("/push/amazon/batch")
def push_amazon_price_batch(body: PushAmazonBatchRequest) -> Dict[str, Any]:
    """Batch publish prices to Amazon with guardrails and dry-run support.

    Each item can specify product_id/asin/sku and an optional price and currency.
    If price is omitted, the single-item endpoint logic resolves it from simulation/listing/history.
    """
    successes: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    for it in body.items:
        try:
            single = PushAmazonRequest(
                product_id=it.product_id,
                asin=it.asin,
                sku=it.sku,
                price=it.price,
                currency=it.currency or "USD",
                dry_run=body.dry_run,
            )
            res = push_amazon_price(single)  # reuse logic; may raise HTTPException
            successes.append({
                "sku": res.get("sku"),
                "price": res.get("price"),
                "dry_run": res.get("dry_run", False),
                "ok": True,
            })
        except HTTPException as he:  # capture and continue
            errors.append({
                "item": it.model_dump(),
                "status": he.status_code,
                "detail": he.detail,
            })
        except Exception as e:  # pragma: no cover
            errors.append({
                "item": it.model_dump(),
                "status": 500,
                "detail": str(e),
            })

    return {"ok": len(errors) == 0, "successes": successes, "errors": errors}


@router.get("/guardrails/preview")
def guardrails_preview(
    product_id: Optional[int] = None,
    asin: Optional[str] = None,
    sku: Optional[str] = None,
) -> Dict[str, Any]:
    """Preview pricing guardrails for a product.

    Returns:
      - floor_price_by_margin: minimum price to satisfy margin floor (if supplier cost known)
      - last_price: current listing price or most recent price history
      - max_delta_pct: allowed absolute delta percent
      - allowed_band: [min_allowed_by_delta, max_allowed_by_delta] (if last_price known)
      - recommended_min_safe_price: max(floor_price_by_margin, min_allowed_by_delta)
    """
    with next(get_db()) as session:
        # Resolve product
        prod: Optional[Product] = None
        if product_id is not None:
            prod = session.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
        elif asin:
            prod = session.execute(select(Product).where(Product.asin == asin)).scalar_one_or_none()
        elif sku:
            prod = session.execute(select(Product).where(Product.sku == sku)).scalar_one_or_none()
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")

        # Load guardrails config
        cfg = load_guardrails()
        pguard = PriceGuardrails()
        try:
            pguard.min_net_margin_pct = float(getattr(cfg, "min_net_margin_pct", pguard.min_net_margin_pct))
        except Exception:
            pass

        # Supplier lowest active cost
        supplier_cost: Optional[float] = None
        offer = (
            session.query(SupplierOffer)
            .filter(SupplierOffer.product_id == prod.id, SupplierOffer.active == True)
            .order_by(SupplierOffer.cost.asc())
            .first()
        )
        if offer:
            supplier_cost = float(offer.cost)

        # Compute floor price by margin if cost known
        floor_price_by_margin: Optional[float] = None
        if supplier_cost is not None:
            m = pguard.min_net_margin_pct / 100.0
            k = 1.0 - pguard.platform_fee_pct - pguard.return_reserve_pct
            numer = supplier_cost + (pguard.est_shipping_flat if pguard.free_shipping_enabled else 0.0)
            denom = k - m
            if denom > 0:
                floor_price_by_margin = round(numer / denom, 2)

        # Determine last price (listing preferred, else recent history)
        last_price: Optional[float] = None
        cl = (
            session.query(ChannelListing)
            .filter(ChannelListing.product_id == prod.id, ChannelListing.channel == "amazon")
            .first()
        )
        if cl and cl.price is not None:
            last_price = float(cl.price)
        if last_price is None:
            ph = (
                session.query(PriceHistory)
                .filter(PriceHistory.product_id == prod.id, PriceHistory.channel == "amazon")
                .order_by(PriceHistory.recorded_at.desc())
                .first()
            )
            if ph and ph.price is not None:
                last_price = float(ph.price)

        # Delta band
        try:
            max_delta_pct = float(os.getenv("MAX_PRICE_DELTA_PCT", "20"))
        except Exception:
            max_delta_pct = 20.0
        min_allowed_by_delta: Optional[float] = None
        max_allowed_by_delta: Optional[float] = None
        if last_price is not None and last_price > 0:
            band = max_delta_pct / 100.0
            min_allowed_by_delta = round(last_price * (1.0 - band), 2)
            max_allowed_by_delta = round(last_price * (1.0 + band), 2)

        # Recommended min safe price
        recommended_min_safe_price: Optional[float] = None
        candidates: List[float] = []
        if floor_price_by_margin is not None:
            candidates.append(floor_price_by_margin)
        if min_allowed_by_delta is not None:
            candidates.append(min_allowed_by_delta)
        if candidates:
            recommended_min_safe_price = round(max(candidates), 2)

        return {
            "product": {
                "id": prod.id,
                "sku": prod.sku,
                "asin": prod.asin,
                "brand": prod.brand,
            },
            "guardrails": {
                "min_net_margin_pct": pguard.min_net_margin_pct,
                "platform_fee_pct": pguard.platform_fee_pct,
                "return_reserve_pct": pguard.return_reserve_pct,
                "est_shipping_flat": pguard.est_shipping_flat if pguard.free_shipping_enabled else 0.0,
                "max_delta_pct": max_delta_pct,
            },
            "floor_price_by_margin": floor_price_by_margin,
            "last_price": last_price,
            "allowed_band": [min_allowed_by_delta, max_allowed_by_delta],
            "recommended_min_safe_price": recommended_min_safe_price,
        }
