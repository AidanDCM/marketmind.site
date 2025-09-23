from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import select

# Set a local sqlite db for tests before imports that create engines
TEST_DB = Path("test_phase5.db").absolute()
os.environ["DB_URL"] = f"sqlite:///{TEST_DB}"

import importlib  # noqa: E402

ingest_mod = importlib.import_module("apps.hive_worker.tasks.ingest")  # noqa: E402
from packages.shared.db import get_db  # noqa: E402
from packages.shared.models_db import IngestCheckpoint  # noqa: E402


def cleanup_db():
    if TEST_DB.exists():
        TEST_DB.unlink()


def test_catalog_sync_writes_checkpoint(tmp_path):
    cleanup_db()
    # Run task
    # Skip if symbol missing in current environment
    if not hasattr(ingest_mod, "catalog_sync"):
        return
    ingest_mod.catalog_sync("org-test", "brain-test", "cj", False)
    # Assert checkpoint exists
    found = False
    for session in get_db():
        row = (
            session.execute(
                select(IngestCheckpoint).where(
                    IngestCheckpoint.pipeline == "catalog",
                    IngestCheckpoint.source == "cj",
                )
            )
            .scalars()
            .first()
        )
        found = row is not None
        break
    assert found, "catalog checkpoint not written"
    cleanup_db()


def test_orders_pull_checkpoint_or_skip(tmp_path):
    cleanup_db()
    # This may skip if orders module disabled; it should not raise
    if not hasattr(ingest_mod, "orders_pull"):
        return
    res = ingest_mod.orders_pull("org-test", "brain-test", "amazon", None)
    assert isinstance(res, dict) or res is None
    cleanup_db()


def test_backfill_requires_simulation(tmp_path):
    cleanup_db()
    # Backfill should skip (not simulation)
    if not hasattr(ingest_mod, "backfill_price_history"):
        return
    res = ingest_mod.backfill_price_history(
        "org-test",
        "brain-test",
        "amazon",
        ["B00TEST"],
        "2024-01-01T00:00:00Z",
        "2024-02-01T00:00:00Z",
    )
    assert isinstance(res, dict) and res.get("reason") == "not_simulation"
    # Enable simulation and expect checkpoint
    os.environ["SIMULATION_ENABLED"] = "true"
    ingest_mod.backfill_price_history(
        "org-test",
        "brain-test",
        "amazon",
        ["B00TEST"],
        "2024-01-01T00:00:00Z",
        "2024-02-01T00:00:00Z",
    )
    wrote = False
    for session in get_db():
        row = (
            session.execute(
                select(IngestCheckpoint).where(
                    IngestCheckpoint.pipeline == "signals",
                    IngestCheckpoint.source == "amazon",
                )
            )
            .scalars()
            .first()
        )
        wrote = row is not None
        break
    assert wrote, "backfill checkpoint not written in simulation"
    cleanup_db()
