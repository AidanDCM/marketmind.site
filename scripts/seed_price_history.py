#!/usr/bin/env python3
import sys

from sqlalchemy import inspect, text

from packages.shared.db import get_engine

"""
Seed one price_history row depending on detected schema.
- If table has (product_id, channel, price, source, recorded_at): insert referencing an existing product.
- If table has (org_id, listing_id, ...): require dependent tables/rows (org, channel_listing). If missing, skip with message.

Exits 0 with a human-readable message even when skipping, so it's safe in Makefile.
"""


def main():
    engine = get_engine()
    insp = inspect(engine)
    if "price_history" not in insp.get_table_names():
        print("price_history not present; skipping seeding")
        return 0

    cols = {c["name"] for c in insp.get_columns("price_history")}

    with engine.begin() as conn:
        # Variant A: simple product-based schema
        if {"product_id", "channel", "price", "source", "recorded_at"}.issubset(cols):
            # ensure at least one product exists
            pid = conn.execute(text("SELECT id FROM products ORDER BY id LIMIT 1")).scalar()
            if not pid:
                print("No products found; seeding one first for price_history...")
                conn.execute(
                    text(
                        """
                    INSERT INTO products (sku, asin, title, brand, images, created_at, updated_at)
                    VALUES ('SKU-SEED-PH', 'B000SEEDPH', 'Seed Product', 'SeedBrand', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """
                    )
                )
                pid = conn.execute(text("SELECT id FROM products WHERE sku='SKU-SEED-PH'")).scalar()
            conn.execute(
                text(
                    """
                INSERT INTO price_history (product_id, channel, price, source, recorded_at)
                VALUES (:pid, 'amazon', 19.99, 'seed', CURRENT_TIMESTAMP)
                """
                ),
                {"pid": pid},
            )
            print("Seeded price_history (product-based) for product_id:", pid)
            return 0

        # Variant B: partitioned/legacy listing-based schema (org_id, listing_id)
        if {"org_id", "listing_id", "price_cents", "source", "recorded_at"}.issubset(cols):
            tables = set(insp.get_table_names())
            has_org = "org" in tables
            has_channel_listing = "channel_listing" in tables  # singular
            if not has_org or not has_channel_listing:
                print(
                    "price_history appears listing-based but dependencies missing:",
                    "org present" if has_org else "org MISSING",
                    ",",
                    "channel_listing present" if has_channel_listing else "channel_listing MISSING",
                    "\nSkipping seeding to avoid broken FKs.",
                )
                return 0
            # If both exist, try to find a listing row and org row
            org_id = conn.execute(text("SELECT id FROM org ORDER BY created_at LIMIT 1")).scalar()
            listing_id = conn.execute(
                text("SELECT id FROM channel_listing ORDER BY id LIMIT 1")
            ).scalar()
            if not org_id or not listing_id:
                print(
                    "Required rows missing in org/channel_listing; skipping price_history seeding."
                )
                return 0
            conn.execute(
                text(
                    """
                INSERT INTO price_history (org_id, listing_id, price_cents, buybox, comp_best_cents, source, recorded_at, meta, id, created_at, updated_at)
                VALUES (:org_id, :listing_id, 1999, 0, NULL, 'seed', CURRENT_TIMESTAMP, '{}', hex(randomblob(16)), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                ),
                {"org_id": org_id, "listing_id": listing_id},
            )
            print("Seeded price_history (listing-based) for listing_id:", listing_id)
            return 0

        print("price_history schema not recognized for automatic seeding; skipping.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
