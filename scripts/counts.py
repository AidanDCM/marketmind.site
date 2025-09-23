from __future__ import annotations

import sys
from typing import Dict, List

from sqlalchemy import inspect, text

# Use the shared Session factory to ensure we connect to the same DB as the app/migrations
from packages.shared.db import get_engine


def count_from_first_existing_table(engine, candidates: List[str]) -> int | None:
    insp = inspect(engine)
    existing = set(insp.get_table_names())
    for name in candidates:
        if name in existing:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) AS c FROM {name}"))
                row = result.first()
                return int(row[0]) if row is not None else 0
    return None


def main() -> int:
    # Define labels to candidate table names (ordered by preference)
    targets: Dict[str, List[str]] = {
        "Products": ["products", "product"],
        "Suppliers": ["suppliers", "supplier_offer", "supplier"],
        "Competitors": ["competitors", "competitor"],
        "PriceHistory": ["price_history"],
    }

    # Ensure engine/session initializes using current env/config
    engine = get_engine()

    any_missing = False
    for label, candidates in targets.items():
        cnt = count_from_first_existing_table(engine, candidates)
        if cnt is None:
            any_missing = True
            print(f"{label}: n/a (missing table: tried {', '.join(candidates)})")
        else:
            print(f"{label}: {cnt}")

    # Close any pooled connections
    engine.dispose()

    # If some tables are missing, still exit 0 to keep this diagnostic non-fatal.
    return 0


if __name__ == "__main__":
    sys.exit(main())
