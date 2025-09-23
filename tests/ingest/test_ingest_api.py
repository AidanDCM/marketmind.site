from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient
from unittest.mock import patch

# Use dedicated sqlite file for API tests
TEST_DB = Path("test_ingest_api.db").absolute()
os.environ["DB_URL"] = f"sqlite:///{TEST_DB}"
os.environ["APP_ENV"] = "dev"
os.environ["SIMULATION_ENABLED"] = "false"

from apps.hive_api.main import app  # noqa: E402

client = TestClient(app)


def cleanup_db():
    if TEST_DB.exists():
        TEST_DB.unlink()


def test_status_endpoint_works():
    cleanup_db()
    r = client.get("/ingest/status")
    assert r.status_code == 200
    body = r.json()
    assert "checkpoints" in body


def test_enqueues_catalog_and_signals_and_orders_routes():
    cleanup_db()

    class FakeTask:
        def __init__(self):
            self.id = "test-task-id"

    with patch("apps.hive_api.routers.ingest.celery_app.send_task", return_value=FakeTask()):
        # Catalog
        rc = client.post("/ingest/run/catalog", json={"supplier": "cj"})
        assert rc.status_code == 200
        assert rc.json().get("status") == "queued"

        # Signals
        rs = client.post("/ingest/run/signals", json={"channel": "amazon"})
        assert rs.status_code == 200
        assert rs.json().get("status") == "queued"

        # Orders - may be disabled -> expect 400 or queued
        ro = client.post("/ingest/run/orders", json={"channel": "amazon"})
        assert ro.status_code in (200, 400)


def test_backfill_requires_simulation_flag_and_replay_checkpoint():
    cleanup_db()

    # Backfill requires simulation -> expect 400
    class FakeTask:
        def __init__(self):
            self.id = "test-task-id"

    with (
        patch("apps.hive_api.routers.ingest.celery_app.send_task", return_value=FakeTask()),
        patch("apps.hive_api.routers.ingest.is_simulation", return_value=False),
    ):
        rb = client.post(
            "/ingest/backfill/price_history",
            json={
                "channel": "amazon",
                "asins": ["B00TEST"],
                "start_iso": "2024-01-01T00:00:00Z",
                "end_iso": "2024-02-01T00:00:00Z",
            },
        )
    assert rb.status_code == 400

    # Replay checkpoint should succeed
    rr = client.post(
        "/ingest/replay/checkpoint",
        json={
            "pipeline": "signals",
            "source": "amazon",
            "key": "manual",
            "value": "2025-01-01T00:00:00Z",
        },
    )
    assert rr.status_code == 200
    assert rr.json().get("status") == "ok"

    cleanup_db()
