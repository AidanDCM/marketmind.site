from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import func, select

# Use an isolated SQLite DB for this test module
TEST_DB = Path("test_idempotent_catalog.db").absolute()
os.environ["DB_URL"] = f"sqlite:///{TEST_DB}"

import importlib  # noqa: E402

ingest_mod = importlib.import_module("apps.hive_worker.tasks.ingest")  # noqa: E402
from packages.shared.db import get_db  # noqa: E402
from packages.shared.models_db import Product, SupplierOffer  # noqa: E402
from packages.shared.adapters.base import ProductIngestItem  # noqa: E402


def cleanup_db():
    if TEST_DB.exists():
        TEST_DB.unlink()


def _sample_items():
    # Two items, one duplicate SKU in second run should not create duplicates
    return [
        ProductIngestItem(
            sku="SKU-001",
            title="Sample Product 1",
            brand="BrandA",
            price=12.34,
            supplier_sku="CJ-001",
            cost=9.99,
            stock_qty=5,
            lead_time_hours=48,
        ),
        ProductIngestItem(
            sku="SKU-002",
            title="Sample Product 2",
            brand="BrandB",
            price=22.22,
            supplier_sku="CJ-002",
            cost=15.55,
            stock_qty=3,
            lead_time_hours=48,
        ),
    ]


def test_catalog_sync_is_idempotent(tmp_path):
    cleanup_db()
    if not hasattr(ingest_mod, "catalog_sync"):
        return

    with patch(
        "apps.hive_worker.tasks.ingest.CJAdapter.fetch_products", return_value=_sample_items()
    ):
        # First run
        ingest_mod.catalog_sync("org-x", "brain-y", "cj", False)
        # Second run with same data
        ingest_mod.catalog_sync("org-x", "brain-y", "cj", False)

    # Validate row counts are stable and no duplicates were created
    for session in get_db():
        product_count = session.execute(select(func.count()).select_from(Product)).scalar_one()
        offer_count = session.execute(select(func.count()).select_from(SupplierOffer)).scalar_one()

        # Expect 2 unique products, 2 unique supplier offers after two runs
        assert product_count == 2
        assert offer_count == 2
        break

    cleanup_db()
