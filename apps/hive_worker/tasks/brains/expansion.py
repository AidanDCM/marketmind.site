from typing import Any, Dict

from apps.hive_worker.celery_app import app
from packages.database.models import DecisionLog, SessionLocal


@app.task(name="apps.hive_worker.tasks.brains.expansion.score_market")
def score_market(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Score new market/channel/supplier expansion opportunities.
    Stub implementation.
    """
    market = payload.get("market", "us")
    score = 0.5

    # Best-effort decision logging (audit)
    try:
        db = SessionLocal()
        log = DecisionLog(
            brain="expansion",
            decision_id=payload.get("decision_id"),
            product_id=None,
            order_id=None,
            context={"payload": payload},
            decision={"market": market, "score": score},
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
        "task": "score_market",
        "market": market,
        "score": score,
    }
