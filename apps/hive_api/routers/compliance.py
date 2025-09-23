from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.hive_api.security import SubjectScope, get_subject_scope_optional
from apps.hive_worker.celery_app import app as celery_app
from packages.database.models import (
    CompliancePack,
    ComplianceViolation,
    ListingComplianceState,
    SupplierWhitelist,
)
from packages.shared.config.audit import log_config_change
from packages.shared.db import get_db

router = APIRouter()


class CompilePackBody(BaseModel):
    name: str
    scope: str = "global"
    version: str = "v1"
    source_uri: str = ""
    enabled: bool = True


class PrepublishListing(BaseModel):
    listing_ref: str
    channel: str
    title: str
    description: str
    images: list[str] = []
    price_cents: int
    category_code: str


class PrepublishLintBody(BaseModel):
    listings: list[PrepublishListing]


class PostpublishScanBody(BaseModel):
    limit: int = 200


class DropshipValidationBody(BaseModel):
    order_id: str
    supplier_id: int


class SupplierWhitelistBody(BaseModel):
    supplier_id: int
    supplier_name: str
    status: str = "approved"
    risk_score: Optional[int] = None
    notes: str = ""


@router.get("/compliance/packs", response_model=List[dict])
def list_packs(db: Session = Depends(get_db)) -> List[dict]:
    packs = db.query(CompliancePack).order_by(CompliancePack.id.desc()).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "scope": p.scope,
            "version": p.version,
            "enabled": p.enabled,
            "source_uri": p.source_uri,
            "created_at": p.created_at,
        }
        for p in packs
    ]


@router.post("/compliance/packs/compile", response_model=dict)
def compile_pack(
    body: CompilePackBody,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
) -> dict:
    # RBAC: only operator/admin may compile packs
    scope.require_role(["operator", "admin"])
    # Minimal stub: just writes a CompliancePack row (compiler service to be enhanced)
    pack = CompliancePack(
        name=body.name,
        scope=body.scope,
        version=body.version,
        enabled=body.enabled,
        source_uri=body.source_uri or "",
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)
    # Audit
    log_config_change(
        actor=scope.sub,
        key=f"compliance.pack.{pack.id}.compile",
        old_value=None,
        new_value={
            "name": pack.name,
            "scope": pack.scope,
            "version": pack.version,
            "enabled": pack.enabled,
            "source_uri": pack.source_uri,
        },
        change_type="create",
        metadata={"pack_id": pack.id},
    )
    # Enqueue background compile to populate terms/categories
    try:
        task = celery_app.send_task(
            "apps.hive_worker.tasks.compliance.compile_pack",
            args=[pack.id, pack.source_uri],
            queue="q.backfill",
        )
        return {"status": "queued", "pack_id": pack.id, "task_id": task.id}
    except Exception as e:
        # Non-fatal in dev/CI: allow API to succeed without broker
        return {
            "status": "skipped",
            "reason": "celery_unavailable",
            "pack_id": pack.id,
            "error": str(e),
        }


@router.post("/compliance/lint/prepublish", response_model=dict)
def prepublish_lint(
    body: PrepublishLintBody,
    scope: SubjectScope = Depends(get_subject_scope_optional),
) -> dict:
    # RBAC: services/operator/admin can call lint before publishing
    scope.require_role(["service", "operator", "admin"])
    try:
        task = celery_app.send_task(
            "apps.hive_worker.tasks.lint.pre_publish_lint",
            args=[[item.dict() for item in body.listings]],
            queue="q.backfill",
        )
        return {"status": "queued", "task_id": task.id}
    except Exception as e:
        return {"status": "skipped", "reason": "celery_unavailable", "error": str(e)}


@router.post("/compliance/scan/postpublish", response_model=dict)
def run_postpublish_scan(
    body: PostpublishScanBody,
    scope: SubjectScope = Depends(get_subject_scope_optional),
) -> dict:
    # RBAC: only operator/admin may trigger an ad-hoc scan
    scope.require_role(["operator", "admin"])
    try:
        task = celery_app.send_task(
            "apps.hive_worker.tasks.lint.scan_post_publish",
            args=[int(body.limit)],
            queue="q.backfill",
        )
        return {"status": "queued", "task_id": task.id}
    except Exception as e:
        return {"status": "skipped", "reason": "celery_unavailable", "error": str(e)}


@router.post("/compliance/dropship/validate", response_model=dict)
def validate_dropship_order(
    body: DropshipValidationBody,
    scope: SubjectScope = Depends(get_subject_scope_optional),
) -> dict:
    # RBAC: only operator/admin may validate dropship orders
    scope.require_role(["operator", "admin"])
    try:
        task = celery_app.send_task(
            "apps.hive_worker.tasks.lint.validate_dropship_order",
            args=[body.order_id, body.supplier_id],
            queue="q.backfill",
        )
        return {"status": "queued", "task_id": task.id, "order_id": body.order_id}
    except Exception as e:
        return {"status": "skipped", "reason": "celery_unavailable", "error": str(e)}


@router.post("/compliance/suppliers/whitelist", response_model=dict)
def add_supplier_whitelist(
    body: SupplierWhitelistBody,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
) -> dict:
    # RBAC: only operator/admin may manage supplier whitelist
    scope.require_role(["operator", "admin"])

    # Check if supplier already exists
    existing = (
        db.query(SupplierWhitelist)
        .filter(SupplierWhitelist.supplier_id == body.supplier_id)
        .first()
    )

    if existing:
        # Update existing
        existing.supplier_name = body.supplier_name
        existing.status = body.status
        existing.risk_score = body.risk_score
        existing.notes = body.notes
        existing.approved_by = scope.sub
        existing.approved_at = datetime.utcnow()
        db.commit()

        log_config_change(
            actor=scope.sub,
            key=f"compliance.supplier_whitelist.{existing.id}.update",
            old_value=None,
            new_value={"status": body.status, "risk_score": body.risk_score},
            change_type="update",
            metadata={"supplier_id": body.supplier_id},
        )

        return {"status": "updated", "id": existing.id, "supplier_id": body.supplier_id}
    else:
        # Create new
        whitelist_entry = SupplierWhitelist(
            supplier_id=body.supplier_id,
            supplier_name=body.supplier_name,
            status=body.status,
            risk_score=body.risk_score,
            approved_by=scope.sub,
            notes=body.notes,
        )
        db.add(whitelist_entry)
        db.commit()
        db.refresh(whitelist_entry)

        log_config_change(
            actor=scope.sub,
            key=f"compliance.supplier_whitelist.{whitelist_entry.id}.create",
            old_value=None,
            new_value={"supplier_id": body.supplier_id, "status": body.status},
            change_type="create",
            metadata={"supplier_id": body.supplier_id},
        )

        return {"status": "created", "id": whitelist_entry.id, "supplier_id": body.supplier_id}


@router.get("/compliance/suppliers/whitelist", response_model=List[dict])
def list_supplier_whitelist(
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[dict]:
    q = db.query(SupplierWhitelist).order_by(SupplierWhitelist.id.desc())
    if status:
        q = q.filter(SupplierWhitelist.status == status)
    rows = q.limit(min(limit, 1000)).all()
    return [
        {
            "id": r.id,
            "supplier_id": r.supplier_id,
            "supplier_name": r.supplier_name,
            "status": r.status,
            "risk_score": r.risk_score,
            "approved_by": r.approved_by,
            "approved_at": r.approved_at,
        }
        for r in rows
    ]


@router.get("/compliance/violations", response_model=List[dict])
def list_violations(
    channel: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[dict]:
    q = db.query(ComplianceViolation).order_by(ComplianceViolation.id.desc())
    if channel:
        q = q.filter(ComplianceViolation.channel == channel)
    rows = q.limit(min(limit, 1000)).all()
    return [
        {
            "id": r.id,
            "ts": r.ts,
            "channel": r.channel,
            "listing_ref": r.listing_ref,
            "vtype": r.vtype,
            "severity": r.severity,
            "action": r.action,
        }
        for r in rows
    ]


@router.get("/compliance/listings/state", response_model=List[dict])
def list_listing_state(
    org_id: Optional[str] = None,
    brain_id: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[dict]:
    q = db.query(ListingComplianceState).order_by(ListingComplianceState.id.desc())
    if org_id:
        q = q.filter(ListingComplianceState.org_id == org_id)
    if brain_id:
        q = q.filter(ListingComplianceState.brain_id == brain_id)
    if channel:
        q = q.filter(ListingComplianceState.channel == channel)
    rows = q.limit(min(limit, 1000)).all()
    return [
        {
            "id": r.id,
            "org_id": r.org_id,
            "brain_id": r.brain_id,
            "product_id": r.product_id,
            "channel": r.channel,
            "listing_ref": r.listing_ref,
            "state": r.state,
            "last_reviewed_at": r.last_reviewed_at,
        }
        for r in rows
    ]
