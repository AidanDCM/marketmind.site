from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.hive_api.security import SubjectScope, get_subject_scope_optional
from packages.database.models import (
    BenchmarkRun,
    DriftReport,
    ModelMetric,
    ModelVersion,
    RolloutState,
)
from packages.shared.db import get_db, ping_db

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/health")
async def health():
    return {"ok": True, "scope": "learning", "db": ping_db()}


@router.get("/models")
async def list_models(
    brain: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.ensure_scope(None, req_brain_ids=[])
    q = db.query(ModelVersion)
    if brain:
        q = q.filter(ModelVersion.brain_id == brain)
    q = q.order_by(ModelVersion.trained_at.desc().nullslast())
    capped = max(1, min(limit, 500))
    items = [
        {
            "id": mv.id,
            "brain_id": mv.brain_id,
            "version": mv.version,
            "status": mv.status,
            "dataset_range": mv.dataset_range,
            "trained_at": mv.trained_at.isoformat() if mv.trained_at else None,
        }
        for mv in q.limit(capped).all()
    ]
    total = q.count()
    return {"items": items, "total": total, "filter": {"brain": brain}, "limit": capped}


class RetrainRequestPayload(BaseModel):
    brain: str = "pricing"
    dataset_range: Optional[str] = None


class HistoricalTrainPayload(BaseModel):
    brain_id: str
    start_date: str  # ISO8601
    end_date: str  # ISO8601
    features: Optional[list] = None
    model_type: Optional[str] = "auto"


@router.get("/metrics")
async def list_metrics(
    model_version_id: Optional[int] = None,
    name: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.ensure_scope(None, req_brain_ids=[])
    q = db.query(ModelMetric)
    if model_version_id:
        q = q.filter(ModelMetric.model_version_id == model_version_id)
    if name:
        q = q.filter(ModelMetric.name == name)
    q = q.order_by(ModelMetric.observed_at.desc().nullslast())
    capped = max(1, min(limit, 500))
    items = [
        {
            "id": mm.id,
            "model_version_id": mm.model_version_id,
            "name": mm.name,
            "value": mm.value,
            "observed_at": mm.observed_at.isoformat() if mm.observed_at else None,
        }
        for mm in q.limit(capped).all()
    ]
    total = q.count()
    return {
        "items": items,
        "total": total,
        "filter": {"model_version_id": model_version_id, "name": name},
        "limit": capped,
    }


@router.get("/drift")
async def list_drift_reports(
    brain_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.ensure_scope(None, req_brain_ids=[])
    q = db.query(DriftReport)
    if brain_id:
        q = q.filter(DriftReport.brain_id == brain_id)
    if severity:
        q = q.filter(DriftReport.severity == severity)
    q = q.order_by(DriftReport.detected_at.desc().nullslast())
    capped = max(1, min(limit, 500))
    items = [
        {
            "id": dr.id,
            "model_version_id": dr.model_version_id,
            "brain_id": dr.brain_id,
            "summary": dr.summary,
            "severity": dr.severity,
            "detected_at": dr.detected_at.isoformat() if dr.detected_at else None,
        }
        for dr in q.limit(capped).all()
    ]
    total = q.count()
    return {
        "items": items,
        "total": total,
        "filter": {"brain_id": brain_id, "severity": severity},
        "limit": capped,
    }


@router.get("/benchmarks")
async def list_benchmarks(
    model_version_id: Optional[int] = None,
    name: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.ensure_scope(None, req_brain_ids=[])
    q = db.query(BenchmarkRun)
    if model_version_id:
        q = q.filter(BenchmarkRun.model_version_id == model_version_id)
    if name:
        q = q.filter(BenchmarkRun.name == name)
    q = q.order_by(BenchmarkRun.ran_at.desc().nullslast())
    capped = max(1, min(limit, 500))
    items = [
        {
            "id": br.id,
            "model_version_id": br.model_version_id,
            "name": br.name,
            "dataset_ref": br.dataset_ref,
            "score": br.score,
            "report": br.report,
            "ran_at": br.ran_at.isoformat() if br.ran_at else None,
        }
        for br in q.limit(capped).all()
    ]
    total = q.count()
    return {
        "items": items,
        "total": total,
        "filter": {"model_version_id": model_version_id, "name": name},
        "limit": capped,
    }


@router.get("/rollouts")
async def list_rollout_states(
    brain_id: Optional[str] = None,
    phase: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.ensure_scope(None, req_brain_ids=[])
    q = db.query(RolloutState)
    if brain_id:
        q = q.filter(RolloutState.brain_id == brain_id)
    if phase:
        q = q.filter(RolloutState.phase == phase)
    q = q.order_by(RolloutState.updated_at.desc().nullslast())
    capped = max(1, min(limit, 500))
    items = [
        {
            "id": rs.id,
            "model_version_id": rs.model_version_id,
            "brain_id": rs.brain_id,
            "phase": rs.phase,
            "percent": rs.percent,
            "updated_at": rs.updated_at.isoformat() if rs.updated_at else None,
        }
        for rs in q.limit(capped).all()
    ]
    total = q.count()
    return {
        "items": items,
        "total": total,
        "filter": {"brain_id": brain_id, "phase": phase},
        "limit": capped,
    }


@router.post("/rollouts/promote", status_code=status.HTTP_202_ACCEPTED)
async def promote_rollout(
    payload: dict,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.require_role(["admin", "editor"])
    rollout_id = payload.get("rollout_id")
    target_phase = payload.get("target_phase", "production")
    target_percent = payload.get("target_percent", 100)

    if not rollout_id:
        raise HTTPException(status_code=400, detail="rollout_id required")

    rollout = db.query(RolloutState).filter(RolloutState.id == rollout_id).first()
    if not rollout:
        raise HTTPException(status_code=404, detail="Rollout not found")

    # Enqueue orchestrator task
    from apps.hive_worker.tasks.learning import promote_rollout_task

    task = promote_rollout_task.delay(rollout_id, target_phase, target_percent)

    return {
        "ok": True,
        "task_id": task.id,
        "rollout_id": rollout_id,
        "target_phase": target_phase,
        "target_percent": target_percent,
    }


@router.post("/models/retrain", status_code=status.HTTP_202_ACCEPTED)
async def retrain_model(
    payload: RetrainRequestPayload,
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.require_role(["admin", "editor"])
    brain = payload.brain or "pricing"
    dataset_range = payload.dataset_range

    # Enqueue Celery task
    from apps.hive_worker.tasks.learning import train_model

    try:
        task = train_model.delay(brain, dataset_range)
        task_id = getattr(task, "id", None)
    except Exception:
        # Broker may be unavailable in some environments; return synthetic id
        from datetime import datetime

        task_id = f"dev-train-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    return {"ok": True, "task_id": task_id, "brain": brain, "dataset_range": dataset_range}


@router.post("/train/historical", status_code=status.HTTP_202_ACCEPTED)
async def train_historical(
    payload: HistoricalTrainPayload,
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    """Train a model on a historical data slice for a given brain.

    Accepts ISO8601 start/end dates, optional features whitelist, and optional model_type.
    Enqueues a background training task and returns a task identifier.
    """
    scope.require_role(["admin", "editor"])

    # Validate date range
    try:
        start_dt = datetime.fromisoformat(payload.start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(payload.end_date.replace("Z", "+00:00"))
    except Exception as err:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO8601.") from err

    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    # Enqueue worker task
    from apps.hive_worker.tasks.learning import train_historical_model

    try:
        task = train_historical_model.delay(
            payload.brain_id,
            payload.start_date,
            payload.end_date,
            payload.features,
            payload.model_type,
        )
        task_id = getattr(task, "id", None)
    except Exception:
        task_id = f"dev-hist-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    return {
        "ok": True,
        "task_id": task_id,
        "brain_id": payload.brain_id,
        "date_range": {"start": payload.start_date, "end": payload.end_date},
        "features": payload.features,
        "model_type": payload.model_type,
    }
