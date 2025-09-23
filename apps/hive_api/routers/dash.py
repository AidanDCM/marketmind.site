from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.hive_api.security import SubjectScope, get_subject_scope_optional
from packages.shared.db import get_db

router = APIRouter(prefix="/dash", tags=["dashboards"])


@router.get("/kpis")
def kpis(
    org_id: Optional[str] = Query(None, description="Organization scope"),
    brain_id: Optional[str] = Query(None, description="Brain scope"),
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    """Return top-level KPIs. Prefers SQL views if present; otherwise computes inline.

    Expected optional views (Postgres):
      - v_dash_sales_kpis (org_id, brain_id, orders, net_revenue_cents, aov_cents)
    Fallbacks are computed against core tables on any dialect.
    """
    # Enforce subject scope
    sub.ensure_scope(req_org_id=org_id, req_brain_ids=[brain_id] if brain_id else [])

    # Try view first
    try:
        res = (
            db.execute(
                text(
                    """
                SELECT org_id, brain_id, orders, net_revenue_cents, aov_cents
                FROM v_dash_sales_kpis
                WHERE (:org_id IS NULL OR org_id = :org_id)
                  AND (:brain_id IS NULL OR brain_id = :brain_id)
                LIMIT 1
                """
                ),
                {"org_id": org_id, "brain_id": brain_id},
            )
            .mappings()
            .first()
        )
        if res:
            return {
                "org_id": res["org_id"],
                "brain_id": res["brain_id"],
                "orders": int(res["orders"] or 0),
                "net_revenue": (int(res["net_revenue_cents"] or 0)) / 100.0,
                "aov": (int(res["aov_cents"] or 0)) / 100.0,
                "source": "view",
            }
    except Exception:
        # View may not exist on SQLite or older schema; fallback below
        pass

    # Fallback: compute from orders table
    res = (
        db.execute(
            text(
                """
            SELECT
              COUNT(*) AS orders,
              COALESCE(SUM(total * 100), 0) AS net_revenue_cents,
              CASE WHEN COUNT(*) > 0 THEN COALESCE(SUM(total * 100),0) / COUNT(*) ELSE 0 END AS aov_cents
            FROM orders
            WHERE 1=1
            """
            ),
            {},
        )
        .mappings()
        .first()
    )

    return {
        "org_id": org_id,
        "brain_id": brain_id,
        "orders": int(res["orders"] or 0),
        "net_revenue": (int(res["net_revenue_cents"] or 0)) / 100.0,
        "aov": (int(res["aov_cents"] or 0)) / 100.0,
        "source": "fallback",
    }


@router.get("/orders/summary")
def orders_summary(
    org_id: Optional[str] = Query(None),
    brain_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    """Orders by status summary."""
    sub.ensure_scope(req_org_id=org_id, req_brain_ids=[brain_id] if brain_id else [])

    rows = (
        db.execute(
            text(
                """
            SELECT status, COUNT(*) AS cnt
            FROM orders
            WHERE 1=1
            GROUP BY status
            ORDER BY status
            """
            ),
            {},
        )
        .mappings()
        .all()
    )

    return {"summary": [{"status": r["status"], "count": int(r["cnt"])} for r in rows]}
