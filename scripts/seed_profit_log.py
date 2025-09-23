#!/usr/bin/env python3
"""
Seed demo rows into profit_modules_log for dashboard visualization.
Idempotent-ish: avoids duplicating the same (module, action) combo in last 10 minutes.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

import os
from packages.database.models import init_db
from packages.database.models.profit import ProfitModuleLog
from packages.database.models.base import SessionLocal


def main() -> None:
    db_url = os.environ.get("DB_URL", "sqlite:///./dev.db")
    init_db(db_url)
    now = datetime.utcnow()
    rows = [
        {
            "timestamp": now - timedelta(minutes=5),
            "module": "bundles",
            "action": "bundle_trial_start",
            "guardrails": {"map": True, "floor_ok": True, "canary_step": 1},
            "outcome": "started",
            "org_id": "org_demo",
            "brain_id": "brain_marketing",
        },
        {
            "timestamp": now - timedelta(minutes=3),
            "module": "coupons",
            "action": "coupon_applied",
            "guardrails": {"effective_price_ge_map": True},
            "outcome": "published",
            "org_id": "org_demo",
            "brain_id": "brain_marketing",
        },
        {
            "timestamp": now - timedelta(minutes=1),
            "module": "pruning",
            "action": "pause_sku",
            "guardrails": {"bottom_pct": 10, "days": 30},
            "outcome": "paused",
            "org_id": "org_demo",
            "brain_id": "brain_pricing",
        },
    ]

    db = SessionLocal()
    try:
        ten_min_ago = now - timedelta(minutes=10)
        for r in rows:
            exists = (
                db.query(ProfitModuleLog)
                .filter(ProfitModuleLog.timestamp >= ten_min_ago)
                .filter(ProfitModuleLog.module == r["module"])
                .filter(ProfitModuleLog.action == r["action"])
                .first()
            )
            if exists:
                continue
            db.add(ProfitModuleLog(**r))
        db.commit()
        print("Seeded profit_modules_log with demo rows.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
