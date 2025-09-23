from typing import Any, Dict

from apps.hive_worker.celery_app import app
from packages.database.models import DecisionLog, SessionLocal


@app.task(name="apps.hive_worker.tasks.brains.compliance.check_order")
def check_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run compliance checks (tax, policy, fraud) for an order/context.
    Stub implementation.
    """
    order_id = payload.get("order_id")
    flags: list[str] = []

    # Best-effort decision logging (audit)
    try:
        db = SessionLocal()
        log = DecisionLog(
            brain="compliance",
            decision_id=payload.get("decision_id"),
            product_id=None,
            order_id=order_id,
            context={"payload": payload},
            decision={"flags": flags, "status": "ok"},
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
        "task": "check_order",
        "order_id": order_id,
        "flags": flags,
        "status": "ok",
    }
