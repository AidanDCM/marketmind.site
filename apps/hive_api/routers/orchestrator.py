from typing import Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException

router = APIRouter()

BrainName = Literal["pricing", "marketing", "analytics", "compliance", "expansion"]

# In-memory freeze state; in production, persist to DB or config store
FROZEN: Dict[str, bool] = {}


@router.get("/orchestrator/health")
def orchestrator_health() -> Dict[str, object]:
    return {
        "service": "orchestrator",
        "status": "ok",
        "frozen": {k: v for k, v in sorted(FROZEN.items())},
    }


@router.get("/orchestrator/queues")
def orchestrator_queues() -> Dict[str, List[str]]:
    # Declared task names by convention; these must match Celery task names
    return {
        "pricing": ["apps.hive_worker.tasks.brains.pricing.price_decide"],
        "marketing": ["apps.hive_worker.tasks.brains.marketing.generate_copy"],
        "analytics": ["apps.hive_worker.tasks.brains.analytics.aggregate_kpis"],
        "compliance": ["apps.hive_worker.tasks.brains.compliance.check_order"],
        "expansion": ["apps.hive_worker.tasks.brains.expansion.score_market"],
    }


@router.post("/orchestrator/freeze/{brain}")
def orchestrator_freeze(brain: BrainName, freeze: bool = True) -> Dict[str, object]:
    FROZEN[brain] = bool(freeze)
    return {"brain": brain, "frozen": FROZEN[brain]}


@router.post("/orchestrator/override")
def orchestrator_override(
    brain: BrainName,
    decision_id: str,
    new_value: str,
    reason: Optional[str] = None,
) -> Dict[str, object]:
    if FROZEN.get(brain, False):
        # Overrides can proceed even if frozen; freeze blocks new autonomous actions
        pass
    # In a future iteration, persist override to SQL + Sheets.
    if not decision_id:
        raise HTTPException(status_code=400, detail="decision_id required")
    return {
        "status": "override-accepted",
        "brain": brain,
        "decision_id": decision_id,
        "new_value": new_value,
        "reason": reason,
    }
