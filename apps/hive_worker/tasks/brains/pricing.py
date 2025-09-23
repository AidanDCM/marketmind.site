from typing import Any, Dict

from apps.hive_worker.celery_app import app
from packages.database.models import DecisionLog, SessionLocal


@app.task(name="apps.hive_worker.tasks.brains.pricing.price_decide")
def price_decide(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Decide price for a product/listing context.
    This is a stub; replace with real logic and persistence.
    """
    product_id = payload.get("product_id")
    decision = {
        "new_price": payload.get("base_price", 10.0),
        "reason": "stub",
    }

    # Best-effort decision logging (audit)
    try:
        db = SessionLocal()
        log = DecisionLog(
            brain="pricing",
            decision_id=payload.get("decision_id"),
            product_id=product_id,
            order_id=None,
            context={"payload": payload},
            decision=decision,
            reason="stub",
        )
        db.add(log)
        db.commit()
    except Exception:
        # Avoid crashing stub tasks if DB not available
        pass
    finally:
        try:
            db.close()  # type: ignore[name-defined]
        except Exception:
            pass

    return {
        "task": "price_decide",
        "product_id": product_id,
        "decision": decision,
    }
