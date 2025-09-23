from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, func

from packages.shared.db import get_db
from packages.shared.models_db import (
    ChannelListing,
    PriceHistory,
    PricingSimulation,
    Product,
    SupplierOffer,
)
from packages.shared.pricing import Guardrails, propose_price
from packages.shared.sheets import SheetsClient

router = APIRouter()


def _cheapest_supplier_cost(session, product_id: int) -> Optional[float]:
    row = (
        session.query(func.min(SupplierOffer.cost))
        .filter(SupplierOffer.product_id == product_id, SupplierOffer.active.is_(True))
        .one()
    )
    return float(row[0]) if row and row[0] is not None else None


def _best_comp_price(session, product_id: int) -> Optional[float]:
    ph = (
        session.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id, PriceHistory.channel == "amazon")
        .order_by(desc(PriceHistory.recorded_at))
        .first()
    )
    return float(ph.price) if ph else None


class SimulateRequest(BaseModel):
    limit: int = 100
    min_net_margin_pct: Optional[float] = None
    max_undercut_step: Optional[float] = None
    respect_map: Optional[bool] = None
    free_shipping_enabled: Optional[bool] = None
    platform_fee_pct: Optional[float] = None
    return_reserve_pct: Optional[float] = None
    est_shipping_flat: Optional[float] = None


@router.post("/simulate")
def simulate_pricing(body: SimulateRequest) -> Dict[str, Any]:
    limit = max(1, min(1000, body.limit))
    created = 0
    errors: List[Dict[str, str]] = []
    guard = Guardrails()
    # apply overrides if provided
    for k in [
        "min_net_margin_pct",
        "max_undercut_step",
        "respect_map",
        "free_shipping_enabled",
        "platform_fee_pct",
        "return_reserve_pct",
        "est_shipping_flat",
    ]:
        v = getattr(body, k)
        if v is not None:
            setattr(guard, k, v)

    for session in get_db():
        products = session.query(Product.id).order_by(Product.id.asc()).limit(limit).all()
        for (pid,) in products:
            try:
                supplier_cost = _cheapest_supplier_cost(session, pid)
                if supplier_cost is None:
                    continue
                best_comp = _best_comp_price(session, pid)
                result = propose_price(best_comp, supplier_cost, guard)
                # persist guardrails used for auditability
                try:
                    inputs = dict(result.get("inputs", {}))
                except Exception:
                    inputs = {}
                guard_dict = {
                    "min_net_margin_pct": guard.min_net_margin_pct,
                    "max_undercut_step": guard.max_undercut_step,
                    "respect_map": guard.respect_map,
                    "free_shipping_enabled": guard.free_shipping_enabled,
                    "platform_fee_pct": guard.platform_fee_pct,
                    "return_reserve_pct": guard.return_reserve_pct,
                    "est_shipping_flat": guard.est_shipping_flat,
                }
                inputs["guardrails"] = guard_dict
                sim = PricingSimulation(
                    product_id=pid,
                    proposed_price=result["proposed_price"],
                    margin_pct=result["margin_pct"],
                    inputs=inputs,
                    status="pending",
                )
                session.add(sim)
                created += 1
            except Exception as e:
                errors.append({"product_id": str(pid), "error": str(e)})
        session.commit()
        break

    return {"ok": True, "created": created, "errors": errors}


@router.get("/pending")
def list_pending(limit: int = 50) -> Dict[str, Any]:
    limit = max(1, min(500, limit))
    out: List[Dict[str, Any]] = []
    for session in get_db():
        rows = (
            session.query(PricingSimulation, Product)
            .join(Product, Product.id == PricingSimulation.product_id)
            .filter(PricingSimulation.status == "pending")
            .order_by(desc(PricingSimulation.created_at))
            .limit(limit)
            .all()
        )
        for sim, prod in rows:
            out.append(
                {
                    "product_id": prod.id,
                    "sku": prod.sku,
                    "asin": prod.asin,
                    "title": prod.title,
                    "proposed_price": sim.proposed_price,
                    "margin_pct": sim.margin_pct,
                    "created_at": sim.created_at.isoformat(),
                }
            )
        break
    return {"pending": out}


class ApproveRequest(BaseModel):
    product_id: int
    proposed_price: Optional[float] = None


@router.post("/push/ebay")
def push_ebay_dry_run(product_id: int) -> Dict[str, Any]:
    """Create/Update a channel_listings draft for eBay with proposed approved price and return a dry-run payload."""
    for session in get_db():
        prod: Optional[Product] = session.query(Product).filter(Product.id == product_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")
        sim = (
            session.query(PricingSimulation)
            .filter(
                PricingSimulation.product_id == product_id, PricingSimulation.status == "approved"
            )
            .order_by(desc(PricingSimulation.created_at))
            .first()
        )
        if not sim:
            raise HTTPException(status_code=400, detail="No approved simulation for product")

        # Upsert ChannelListing for eBay
        cl = (
            session.query(ChannelListing)
            .filter(ChannelListing.product_id == product_id, ChannelListing.channel == "ebay")
            .first()
        )
        if not cl:
            cl = ChannelListing(channel="ebay", product_id=product_id, status="draft")
        cl.price = sim.proposed_price
        cl.listing_ref = cl.listing_ref or "dryrun"
        cl.status = "draft"
        session.add(cl)
        session.commit()

        # Build dry-run payload
        payload = {
            "title": prod.title,
            "sku": prod.sku,
            "price": sim.proposed_price,
            "currency": "USD",
            "condition": "NEW",
            "dispatchTimeMax": 3,
            "shipping": {
                "type": "FLAT",
                "service": "USPSGroundAdvantage",
                "cost": (
                    0.0
                    if (sim.inputs or {}).get("guardrails", {}).get("free_shipping_enabled", True)
                    else (sim.inputs or {}).get("guardrails", {}).get("est_shipping_flat", 4.0)
                ),
            },
            "dry_run": True,
        }
        return {
            "ok": True,
            "channel": "ebay",
            "listing": {"status": cl.status, "ref": cl.listing_ref, "price": cl.price},
            "payload": payload,
        }
    raise HTTPException(status_code=500, detail="DB session error")


@router.post("/unapprove")
def unapprove_simulation(payload: ApproveRequest) -> Dict[str, Any]:
    """Revert the most recent approved simulation for a product back to pending.
    Useful for quick 'undo' actions in the UI.
    """
    for session in get_db():
        sim = (
            session.query(PricingSimulation)
            .filter(
                PricingSimulation.product_id == payload.product_id,
                PricingSimulation.status == "approved",
            )
            .order_by(desc(PricingSimulation.created_at))
            .first()
        )
        if not sim:
            raise HTTPException(status_code=404, detail="No approved simulation found for product")
        sim.status = "pending"
        session.add(sim)
        session.commit()
        return {"ok": True, "product_id": payload.product_id, "status": "pending"}
    raise HTTPException(status_code=500, detail="DB session error")


@router.post("/approve")
def approve_simulation(payload: ApproveRequest) -> Dict[str, Any]:
    for session in get_db():
        sim = (
            session.query(PricingSimulation)
            .filter(
                PricingSimulation.product_id == payload.product_id,
                PricingSimulation.status == "pending",
            )
            .order_by(desc(PricingSimulation.created_at))
            .first()
        )
        if not sim:
            raise HTTPException(status_code=404, detail="No pending simulation found for product")
        if payload.proposed_price is not None:
            sim.proposed_price = payload.proposed_price
        sim.status = "approved"
        session.add(sim)
        session.commit()
        return {"ok": True, "product_id": payload.product_id, "proposed_price": sim.proposed_price}
    raise HTTPException(status_code=500, detail="DB session error")


@router.get("/approved")
def list_approved(limit: int = 50) -> Dict[str, Any]:
    limit = max(1, min(500, limit))
    out: List[Dict[str, Any]] = []
    for session in get_db():
        rows = (
            session.query(PricingSimulation, Product)
            .join(Product, Product.id == PricingSimulation.product_id)
            .filter(PricingSimulation.status == "approved")
            .order_by(desc(PricingSimulation.created_at))
            .limit(limit)
            .all()
        )
        for sim, prod in rows:
            out.append(
                {
                    "product_id": prod.id,
                    "sku": prod.sku,
                    "asin": prod.asin,
                    "title": prod.title,
                    "proposed_price": sim.proposed_price,
                    "margin_pct": sim.margin_pct,
                    "created_at": sim.created_at.isoformat(),
                }
            )
        break
    return {"approved": out}


@router.post("/export/approved-to-sheets")
def export_approved_to_sheets(tab: str = "Approved") -> Dict[str, Any]:
    client = SheetsClient()
    if not client.configured:
        return {"ok": False, "reason": "sheets_not_configured"}
    headers = [
        "product_id",
        "sku",
        "asin",
        "title",
        "proposed_price",
        "margin_pct",
        "guardrails_json",
        "approved_at",
    ]
    rows: List[List[object]] = []
    for session in get_db():
        q = (
            session.query(PricingSimulation, Product)
            .join(Product, Product.id == PricingSimulation.product_id)
            .filter(PricingSimulation.status == "approved")
            .order_by(desc(PricingSimulation.created_at))
            .limit(1000)
        )
        for sim, prod in q.all():
            rows.append(
                [
                    prod.id,
                    prod.sku,
                    prod.asin,
                    prod.title,
                    sim.proposed_price,
                    sim.margin_pct,
                    (sim.inputs or {}).get("guardrails"),
                    sim.created_at.isoformat(),
                ]
            )
        break
    ok = client.append_rows(tab, headers, rows)
    return {"ok": ok, "tab": tab, "rows": len(rows)}


@router.post("/export/inventory-to-sheets")
def export_inventory_to_sheets(tab: str = "Inventory") -> Dict[str, Any]:
    client = SheetsClient()
    if not client.configured:
        return {"ok": False, "reason": "sheets_not_configured"}
    headers = [
        "product_id",
        "sku",
        "title",
        "supplier",
        "cost",
        "stock_qty",
        "lead_time_hours",
        "updated_at",
    ]
    rows: List[List[object]] = []
    for session in get_db():
        products = session.query(Product).order_by(Product.id.asc()).limit(2000).all()
        for p in products:
            # Find cheapest active offer
            offer = (
                session.query(SupplierOffer)
                .filter(SupplierOffer.product_id == p.id, SupplierOffer.active.is_(True))
                .order_by(SupplierOffer.cost.asc())
                .first()
            )
            if not offer:
                continue
            rows.append(
                [
                    p.id,
                    p.sku,
                    p.title,
                    offer.supplier_name,
                    offer.cost,
                    offer.stock_qty,
                    offer.lead_time_hours,
                    datetime.utcnow().isoformat(),
                ]
            )
        break
    ok = client.append_rows(tab, headers, rows)
    return {"ok": ok, "tab": tab, "rows": len(rows)}
