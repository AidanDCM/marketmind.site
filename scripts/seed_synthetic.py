from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.shared.db import Base, get_engine, session_scope
from packages.shared.models_db import Competitor, PriceHistory, Product, SupplierOffer

RANDOM = random.Random(42)

BRANDS = ["Acme", "Globex", "Umbrella", "Soylent", "Initech"]
TITLES = [
    "Deluxe Pet Toy",
    "Premium Grooming Kit",
    "Adjustable Harness",
    "Stainless Bowl",
    "Chew Resistant Leash",
]


def ensure_schema() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)


def seed_products(session: Session, n: int = 10) -> List[int]:
    ids: List[int] = []
    for i in range(n):
        sku = f"SYN-{1000+i}"
        prod = Product(
            sku=sku,
            asin=None,
            title=f"{RANDOM.choice(BRANDS)} {RANDOM.choice(TITLES)}",
            brand=RANDOM.choice(BRANDS),
            images=None,
        )
        session.add(prod)
        session.flush()
        ids.append(prod.id)

        # Supplier offer
        cost = round(RANDOM.uniform(5.0, 25.0), 2)
        offer = SupplierOffer(
            supplier_name="SYNTH",
            supplier_sku=sku,
            product_id=prod.id,
            cost=cost,
            stock_qty=RANDOM.randint(5, 200),
            lead_time_hours=RANDOM.choice([24, 48, 72]),
            ships_from="US",
            active=True,
            meta={"note": "synthetic"},
        )
        session.add(offer)

        # Competitor snapshot
        comp_price = round(cost * RANDOM.uniform(1.2, 1.8), 2)
        comp = Competitor(
            product_id=prod.id,
            channel="amazon",
            asin=None,
            seller="competitor_synth",
            price=comp_price,
        )
        session.add(comp)

        # Price history for competitor
        now = datetime.utcnow()
        for d in range(3):
            session.add(
                PriceHistory(
                    product_id=prod.id,
                    channel="amazon",
                    price=max(0.01, comp_price + RANDOM.uniform(-1.0, 1.0)),
                    source="competitor",
                    recorded_at=now - timedelta(days=(3 - d)),
                )
            )
    return ids


def main() -> None:
    ensure_schema()
    with session_scope() as session:
        # if already seeded, skip
        existing = session.execute(select(Product.id).limit(1)).first()
        if existing:
            print("DB already has products; skipping synthetic seed.")
            return
        ids = seed_products(session, n=10)
        session.commit()
        print({"seeded_products": len(ids)})


if __name__ == "__main__":
    main()
