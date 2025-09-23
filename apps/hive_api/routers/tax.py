from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.hive_api.security import SubjectScope, get_subject_scope_optional
from apps.hive_worker.celery_app import app as celery_app
from packages.database.models import TaxAttestation
from packages.shared.config.audit import log_config_change
from packages.shared.db import get_db

router = APIRouter()


class CreateAttestationBody(BaseModel):
    period: str  # YYYY-MM
    jurisdiction: str
    model: str
    total_tax_cents: int = 0
    attester: str
    evidence_uri: str = ""


@router.get("/tax/attestations", response_model=List[dict])
def list_attestations(db: Session = Depends(get_db)) -> List[dict]:  # noqa: B008
    rows = db.query(TaxAttestation).order_by(TaxAttestation.id.desc()).all()
    return [
        {
            "id": r.id,
            "period": r.period,
            "jurisdiction": r.jurisdiction,
            "model": r.model,
            "total_tax_cents": r.total_tax_cents,
            "attester": r.attester,
            "attested_at": r.attested_at,
            "evidence_uri": r.evidence_uri,
        }
        for r in rows
    ]


@router.post("/tax/attestations", response_model=dict)
def create_attestation(
    body: CreateAttestationBody,
    db: Session = Depends(get_db),  # noqa: B008 - FastAPI dependency injection pattern
    scope: SubjectScope = Depends(get_subject_scope_optional),  # noqa: B008
) -> dict:
    # RBAC: only operator/admin can create attestations
    scope.require_role(["operator", "admin"])
    att = TaxAttestation(
        period=body.period,
        jurisdiction=body.jurisdiction,
        model=body.model,
        total_tax_cents=body.total_tax_cents,
        attester=body.attester,
        evidence_uri=body.evidence_uri or "",
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    # Audit log
    log_config_change(
        actor=scope.sub,
        key=f"tax.attestation.{att.id}.create",
        old_value=None,
        new_value={
            "period": att.period,
            "jurisdiction": att.jurisdiction,
            "model": att.model,
            "total_tax_cents": att.total_tax_cents,
            "attester": att.attester,
        },
        change_type="create",
        metadata={"attestation_id": att.id},
    )
    # Enqueue Sheets echo
    try:
        task = celery_app.send_task(
            "apps.hive_worker.tasks.tax.echo_attestation", args=[att.id], queue="q.backfill"
        )
        return {"id": att.id, "task_id": task.id}
    except Exception as e:
        return {"id": att.id, "enqueue": "skipped", "error": str(e)}
