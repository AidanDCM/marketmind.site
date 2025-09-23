from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter

from packages.database.models.finance.cashflow import CashFlowForecast
from packages.database.models.finance.supplier_invoice import SupplierInvoice
from packages.shared.db import get_db
from packages.shared.models_db import (
    ChannelListing,
    PriceHistory,
    PricingSimulation,
    Product,
    SupplierOffer,
)

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/status")
def demo_status() -> Dict[str, int]:
    out = {"products": 0, "offers": 0, "history": 0, "sims": 0, "invoices": 0, "forecast": 0}
    for session in get_db():
        out["products"] = session.query(Product).count()
        out["offers"] = session.query(SupplierOffer).count()
        out["history"] = session.query(PriceHistory).count()
        out["sims"] = session.query(PricingSimulation).count()
        out["invoices"] = session.query(SupplierInvoice).count()
        out["forecast"] = session.query(CashFlowForecast).count()
        break
    return out


@router.post("/seed")
def seed_demo_data(limit: int = 12) -> Dict[str, object]:
    limit = max(5, min(100, limit))
    now = datetime.utcnow()
    for session in get_db():
        if session.query(Product).count() >= limit:
            return {"status": "skipped", "reason": "already_seeded", "counts": demo_status()}
        for i in range(limit):
            sku = f"DEMO-{1000 + i}"
            asin = f"B0{i:07d}"
            p = Product(sku=sku, asin=asin, title=f"Demo Product {i+1}", brand="Acme")
            session.add(p)
            session.flush()
            session.add(SupplierOffer(supplier_name="demo_supplier", supplier_sku=sku, product_id=p.id, cost=round(6 + (i % 6) * 2.0, 2), stock_qty=80 - (i % 10) * 3, lead_time_hours=24 + (i % 3) * 12, ships_from="US", active=True))
            session.add(ChannelListing(channel="amazon", product_id=p.id, listing_ref=asin, status="draft"))
            base = 19.99 + (i % 4) * 2.5
            for d in range(5):
                ts = now - timedelta(days=4 - d)
                session.add(PriceHistory(product_id=p.id, channel="amazon", price=round(base + d * 0.3, 2), source="demo", recorded_at=ts))
            session.add(PricingSimulation(product_id=p.id, proposed_price=round(base + 1.5, 2), margin_pct=0.15 + (i % 3) * 0.02, inputs={"guardrails": {"free_shipping_enabled": True}}, status="approved" if i % 2 == 0 else "pending"))
        # Finance: a couple invoices and simple forecast rows
        for k in range(3):
            amt = 1000 + k * 200
            session.add(SupplierInvoice(org_id=None, supplier_id=1, invoice_no=f"INV-{800 + k}", invoice_date=(now - timedelta(days=25 * (2 - k))).date().isoformat(), due_date=(now - timedelta(days=25 * (2 - k) - 5)).date().isoformat(), currency="USD", subtotal=float(amt), tax=round(amt * 0.07, 2), total=round(amt * 1.07, 2), status="paid" if k == 0 else ("open" if k == 1 else "overdue")))
        for m in range(6):
            start = (now - timedelta(days=30 * (5 - m))).date().isoformat()
            end = (now - timedelta(days=30 * (5 - m) - 29)).date().isoformat()
            inflow = float(5000 + m * 300)
            outflow = float(3500 + m * 200)
            session.add(CashFlowForecast(org_id=None, period_start=start, period_end=end, inflow=inflow, outflow=outflow, net=inflow - outflow))
        session.commit()
        break
    return {"status": "seeded", "counts": demo_status()}
