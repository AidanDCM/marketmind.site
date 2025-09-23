#!/usr/bin/env python3
from sqlalchemy import text

from packages.shared.db import get_engine

"""
Seeds minimal test data into pluralized ecommerce tables that exist post-Phase 3:
- products
- channel_listings
- suppliers
- competitors
- sales
- pricing_simulations

Skips price_history due to partitioned/legacy schema differences.

Respects DB_URL env via packages.shared.db.get_engine().
"""


def main():
    engine = get_engine()
    with engine.begin() as conn:
        # product
        product = {
            "sku": "SKU-TEST-1",
            "asin": "B000TEST01",
            "title": "Test Product",
            "brand": "TestBrand",
            "images": None,
        }
        conn.execute(
            text(
                """
            INSERT INTO products (sku, asin, title, brand, images, created_at, updated_at)
            VALUES (:sku, :asin, :title, :brand, :images, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            ),
            product,
        )
        # SQLite: fetch last inserted id
        prod_id = conn.execute(
            text("SELECT id FROM products WHERE sku = :sku"), {"sku": product["sku"]}
        ).scalar_one()

        # channel_listings
        conn.execute(
            text(
                """
            INSERT INTO channel_listings (channel, product_id, listing_ref, status, price, shipping_rule, updated_at)
            VALUES (:channel, :product_id, :listing_ref, :status, :price, :shipping_rule, CURRENT_TIMESTAMP)
            """
            ),
            {
                "channel": "amazon",
                "product_id": prod_id,
                "listing_ref": "AMZ-TEST-REF-1",
                "status": "active",
                "price": 19.99,
                "shipping_rule": "standard",
            },
        )

        # suppliers
        conn.execute(
            text(
                """
            INSERT INTO suppliers (supplier_name, supplier_sku, product_id, cost, stock_qty, lead_time_hours, ships_from, active, meta)
            VALUES (:supplier_name, :supplier_sku, :product_id, :cost, :stock_qty, :lead_time_hours, :ships_from, 1, NULL)
            """
            ),
            {
                "supplier_name": "Acme Co",
                "supplier_sku": "ACME-SKU-1",
                "product_id": prod_id,
                "cost": 9.50,
                "stock_qty": 100,
                "lead_time_hours": 48,
                "ships_from": "US-CA",
            },
        )

        # competitors
        conn.execute(
            text(
                """
            INSERT INTO competitors (product_id, channel, asin, seller, price, observed_at)
            VALUES (:product_id, :channel, :asin, :seller, :price, CURRENT_TIMESTAMP)
            """
            ),
            {
                "product_id": prod_id,
                "channel": "amazon",
                "asin": "B000TEST01",
                "seller": "OtherSeller",
                "price": 18.49,
            },
        )

        # sales
        conn.execute(
            text(
                """
            INSERT INTO sales (order_id, product_id, channel, sale_price, fees, shipping_cost, created_at)
            VALUES (:order_id, :product_id, :channel, :sale_price, :fees, :shipping_cost, CURRENT_TIMESTAMP)
            """
            ),
            {
                "order_id": "ORDER-1",
                "product_id": prod_id,
                "channel": "amazon",
                "sale_price": 19.99,
                "fees": 2.50,
                "shipping_cost": 3.99,
            },
        )

        # pricing_simulations
        conn.execute(
            text(
                """
            INSERT INTO pricing_simulations (product_id, proposed_price, margin_pct, inputs, status, created_at)
            VALUES (:product_id, :proposed_price, :margin_pct, NULL, 'pending', CURRENT_TIMESTAMP)
            """
            ),
            {
                "product_id": prod_id,
                "proposed_price": 21.99,
                "margin_pct": 35.0,
            },
        )

    print("Seeded minimal data. Product ID:", prod_id)


if __name__ == "__main__":
    main()
