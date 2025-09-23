from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.hive_api.security import SubjectScope, get_subject_scope_optional
from apps.hive_worker.celery_app import app as celery_app
from packages.database.models import ErasureJob, PrivacyRequest
from packages.shared.config.audit import log_config_change
from packages.shared.db import get_db

router = APIRouter()


class CreatePrivacyRequestBody(BaseModel):
    rtype: str  # sar|deletion|erasure
    subject_ref: str
    channel: Optional[str] = None
    notes: str = ""


@router.get("/privacy/requests", response_model=List[dict])
def list_privacy_requests(
    subject_ref: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),  # noqa: B008 - FastAPI dependency injection pattern
) -> List[dict]:
    q = db.query(PrivacyRequest).order_by(PrivacyRequest.id.desc())
    if subject_ref:
        q = q.filter(PrivacyRequest.subject_ref == subject_ref)
    rows = q.limit(min(limit, 1000)).all()
    return [
        {
            "id": r.id,
            "ts": r.ts,
            "rtype": r.rtype,
            "subject_ref": r.subject_ref,
            "channel": r.channel,
            "status": r.status,
            "result_uri": r.result_uri,
        }
        for r in rows
    ]


@router.post("/privacy/requests", response_model=dict)
def create_privacy_request(
    body: CreatePrivacyRequestBody,
    db: Session = Depends(get_db),  # noqa: B008 - FastAPI dependency injection pattern
    scope: SubjectScope = Depends(get_subject_scope_optional),  # noqa: B008
) -> dict:
    # RBAC: only operator/admin can create requests
    scope.require_role(["operator", "admin"])
    pr = PrivacyRequest(
        rtype=body.rtype,
        subject_ref=body.subject_ref,
        channel=body.channel,
        notes=body.notes,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    # Audit log
    log_config_change(
        actor=scope.sub,
        key=f"privacy.request.{pr.id}.create",
        old_value=None,
        new_value={
            "rtype": pr.rtype,
            "subject_ref": pr.subject_ref,
            "channel": pr.channel,
        },
        change_type="create",
        metadata={"request_id": pr.id},
    )
    # Enqueue SAR export if applicable
    if pr.rtype == "sar":
        try:
            task = celery_app.send_task(
                "apps.hive_worker.tasks.privacy.sar_export", args=[pr.id], queue="q.backfill"
            )
            return {"id": pr.id, "status": pr.status, "task_id": task.id}
        except Exception as e:
            return {"id": pr.id, "status": pr.status, "enqueue": "skipped", "error": str(e)}
    return {"id": pr.id, "status": pr.status}


class CreateErasureJobBody(BaseModel):
    request_id: int
    target: str  # dtc|marketplace|sheets


@router.post("/privacy/erasure/jobs", response_model=dict)
def create_erasure_job(
    body: CreateErasureJobBody,
    db: Session = Depends(get_db),  # noqa: B008 - FastAPI dependency injection pattern
    scope: SubjectScope = Depends(get_subject_scope_optional),  # noqa: B008
) -> dict:
    # RBAC: only operator/admin can create erasure jobs
    scope.require_role(["operator", "admin"])
    job = ErasureJob(request_id=body.request_id, target=body.target)
    db.add(job)
    db.commit()
    db.refresh(job)
    # Audit log
    log_config_change(
        actor=scope.sub,
        key=f"privacy.erasure_job.{job.id}.create",
        old_value=None,
        new_value={"request_id": job.request_id, "target": job.target},
        change_type="create",
        metadata={"job_id": job.id},
    )
    # Enqueue erasure execution
    try:
        task = celery_app.send_task(
            "apps.hive_worker.tasks.privacy.run_erasure", args=[job.id], queue="q.backfill"
        )
        return {"id": job.id, "state": job.state, "task_id": task.id}
    except Exception as e:
        return {"id": job.id, "state": job.state, "enqueue": "skipped", "error": str(e)}


@router.get("/privacy/requests/{request_id}/artifact", response_model=dict)
def get_privacy_artifact(request_id: int, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    pr = db.query(PrivacyRequest).filter(PrivacyRequest.id == request_id).one_or_none()
    if not pr:
        return {"error": "not_found"}
    return {"id": pr.id, "status": pr.status, "result_uri": pr.result_uri}


@router.get("/privacy/erasure/jobs/{job_id}", response_model=dict)
def get_erasure_job(job_id: int, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    job = db.query(ErasureJob).filter(ErasureJob.id == job_id).one_or_none()
    if not job:
        return {"error": "not_found"}
    return {
        "id": job.id,
        "request_id": job.request_id,
        "target": job.target,
        "state": job.state,
        "finished_at": job.finished_at,
        "counts": job.counts,
    }
