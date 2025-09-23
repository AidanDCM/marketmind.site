from typing import Any, Dict

from apps.hive_worker.celery_app import app
from packages.database.models import DecisionLog, SessionLocal


@app.task(name="apps.hive_worker.tasks.brains.marketing.generate_copy")
def generate_copy(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate marketing copy variant for a product/segment.
    Stub implementation.
    """
    product_id = payload.get("product_id")
    segment = payload.get("segment", "default")
    variant = {
        "headline": "Amazing Product",
        "body": "This is a stub copy variant.",
    }

    # Best-effort decision logging (audit)
    try:
        db = SessionLocal()
        log = DecisionLog(
            brain="marketing",
            decision_id=payload.get("decision_id"),
            product_id=product_id,
            order_id=None,
            context={"payload": payload},
            decision={"variant": variant, "segment": segment},
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
        "task": "generate_copy",
        "product_id": product_id,
        "segment": segment,
        "variant": variant,
    }
