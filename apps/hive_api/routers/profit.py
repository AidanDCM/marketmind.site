from typing import Any, Dict

from fastapi import APIRouter, Depends, Query

from packages.shared.db import get_db

router = APIRouter()


@router.get("/log")
def get_profit_log(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),  # noqa: B008 - FastAPI dependency injection pattern
) -> Dict[str, Any]:
    """
    Read-only profit modules log endpoint to back Profit dashboard tiles.
    Returns empty list gracefully if underlying table/view is not available.
    """
    try:
        # Attempt to read from a canonical table/view if it exists.
        # We avoid hard dependency to keep this endpoint safe in dev.
        from sqlalchemy import text

        result = db.execute(
            text(
                """
                SELECT timestamp, module, action, guardrails, outcome
                FROM profit_modules_log
                ORDER BY timestamp DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"limit": limit, "offset": offset},
        )
        rows = [
            {
                "timestamp": r[0],
                "module": r[1],
                "action": r[2],
                "guardrails": r[3],
                "outcome": r[4],
            }
            for r in result.fetchall()
        ]
        total = len(rows)
        return {"items": rows, "total": total, "limit": limit, "offset": offset}
    except Exception:
        # Graceful fallback when table/view is not present
        return {"items": [], "total": 0, "limit": limit, "offset": offset}
