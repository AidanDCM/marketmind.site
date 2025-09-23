from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import create_engine, inspect, text

DB_URL = os.environ.get("DB_URL", "sqlite:///./dev.db")


def main() -> None:
    engine = create_engine(DB_URL, future=True)
    with engine.begin() as conn:
        insp = inspect(conn)
        tables = insp.get_table_names()
        if "price_history_legacy" not in tables:
            print("price_history_legacy not found; nothing to migrate")
            return
        if "price_history" not in tables:
            print("price_history (product-based) not found; aborting migration")
            return
        # Verify channel_listings table exists for listing_id -> product_id mapping
        if "channel_listings" not in tables:
            print("channel_listings not found; cannot map listing_id -> product_id. Aborting.")
            return
        # Migrate rows by joining legacy to channel_listings on listing_id
        rows = (
            conn.execute(
                text(
                    """
            SELECT l.id AS legacy_id,
                   l.listing_id,
                   l.price_cents,
                   l.comp_best_cents,
                   l.source,
                   l.recorded_at,
                   cl.product_id,
                   cl.channel
            FROM price_history_legacy l
            JOIN channel_listings cl ON cl.id = l.listing_id
            ORDER BY l.recorded_at
            """
                )
            )
            .mappings()
            .all()
        )
        inserted = 0
        for r in rows:
            price = (r["price_cents"] or 0) / 100.0
            recorded_at: Optional[str] = r["recorded_at"]
            # Idempotency: skip if an identical row already exists
            exists = conn.execute(
                text(
                    """
                SELECT 1 FROM price_history
                WHERE product_id = :pid AND channel = :channel
                  AND source = :source AND recorded_at = :ts AND price = :price
                LIMIT 1
                """
                ),
                {
                    "pid": r["product_id"],
                    "channel": r["channel"] or "unknown",
                    "source": r["source"] or "legacy",
                    "ts": recorded_at,
                    "price": price,
                },
            ).first()
            if exists:
                continue
            conn.execute(
                text(
                    """
                INSERT INTO price_history (product_id, channel, price, source, recorded_at)
                VALUES (:pid, :channel, :price, :source, :ts)
                """
                ),
                {
                    "pid": r["product_id"],
                    "channel": r["channel"] or "unknown",
                    "price": price,
                    "source": r["source"] or "legacy",
                    "ts": recorded_at,
                },
            )
            inserted += 1
        print(f"Migrated {inserted} legacy price_history rows")


if __name__ == "__main__":
    main()
