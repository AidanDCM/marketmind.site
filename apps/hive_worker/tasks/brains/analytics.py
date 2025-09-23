from typing import Any, Dict

from apps.hive_worker.celery_app import app
from packages.database.models import DecisionLog, SessionLocal


@app.task(name="apps.hive_worker.tasks.brains.analytics.aggregate_kpis")
def aggregate_kpis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate KPIs over a time window.
    Stub implementation.
    """
    window = payload.get("window", "7d")
    result = {"ctr": 0.05, "conversion": 0.02}

    # Best-effort decision logging (audit)
    try:
        db = SessionLocal()
        log = DecisionLog(
            brain="analytics",
            decision_id=payload.get("decision_id"),
            product_id=None,
            order_id=None,
            context={"payload": payload},
            decision={"window": window, "result": result},
            reason="stub",
        )
        db.add(log)
        db.commit()
    except Exception:
        pass
    finally:
        try:
            db.close()  # type: ignore[name-defined]
        except Exception:
            pass

    return {
        "task": "aggregate_kpis",
        "window": window,
        "result": result,
    }
