"""Aggregate ad performance from persisted import batches."""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .db.models import ImportBatchRow

_AD_SOURCES = frozenset({"ad_report", "ad_report_csv", "meta_ads", "google_ads", "tiktok_ads"})


@dataclass(frozen=True)
class AdSpendSummary:
    batch_id: int | None
    source: str
    pulled_at: str
    campaigns: int
    total_spend: float
    total_clicks: int
    total_impressions: int
    total_purchases: int
    total_revenue: float

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "source": self.source,
            "pulled_at": self.pulled_at,
            "campaigns": self.campaigns,
            "total_spend": round(self.total_spend, 2),
            "total_clicks": self.total_clicks,
            "total_impressions": self.total_impressions,
            "total_purchases": self.total_purchases,
            "total_revenue": round(self.total_revenue, 2),
        }


def _f(val: str) -> float:
    try:
        return float(val or 0)
    except ValueError:
        return 0.0


def _i(val: str) -> int:
    try:
        return int(float(val or 0))
    except ValueError:
        return 0


def summarize_latest_ad_batch(engine: Engine) -> AdSpendSummary | None:
    """Return spend totals from the most recent ad import batch, if any."""
    with Session(engine) as session:
        batch = session.scalars(
            select(ImportBatchRow)
            .where(ImportBatchRow.source.in_(_AD_SOURCES))
            .order_by(ImportBatchRow.id.desc())
            .limit(1)
        ).first()
        if batch is None:
            return None

        try:
            rows = json.loads(batch.rows_json or "[]")
        except json.JSONDecodeError:
            return None

    spend = clicks = impressions = purchases = 0.0
    revenue = 0.0
    for row in rows:
        if not isinstance(row, dict):
            continue
        spend += _f(str(row.get("spend", "")))
        clicks += _i(str(row.get("clicks", "")))
        impressions += _i(str(row.get("impressions", "")))
        purchases += _i(str(row.get("purchases", "")))
        revenue += _f(str(row.get("revenue", "")))

    return AdSpendSummary(
        batch_id=batch.id,
        source=batch.source,
        pulled_at=batch.pulled_at,
        campaigns=len(rows),
        total_spend=spend,
        total_clicks=int(clicks),
        total_impressions=int(impressions),
        total_purchases=int(purchases),
        total_revenue=revenue,
    )
