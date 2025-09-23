from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.hive_api.security import SubjectScope, get_subject_scope_optional
from packages.database.models.finance.cashflow import CashFlowForecast
from packages.database.models.finance.ledger_batch import LedgerBatch
from packages.database.models.finance.ledger_entry import LedgerEntry
from packages.database.models.finance.reconciliation import ReconciliationTask
from packages.database.models.finance.supplier_invoice import SupplierInvoice
from packages.shared.db import get_db, get_session_factory, ping_db

router = APIRouter(prefix="/finance", tags=["finance"])

# Optional Sentry for breadcrumbs on finance write operations
try:  # pragma: no cover - optional dependency
    import sentry_sdk  # type: ignore
except Exception:  # pragma: no cover
    sentry_sdk = None  # type: ignore

def _sentry_breadcrumb(level: str, category: str, message: str, data: Optional[dict] = None) -> None:
    if sentry_sdk is None:
        return
    try:  # pragma: no cover
        sentry_sdk.add_breadcrumb(
            type="default",
            category=category,
            message=message,
            level=level,
            data=data or {},
        )
    except Exception:
        pass

def _sentry_capture_message(message: str, level: str = "info", data: Optional[dict] = None) -> None:
    if sentry_sdk is None:
        return
    try:  # pragma: no cover
        if data:
            _sentry_breadcrumb(level=level, category="finance", message=message, data=data)
        sentry_sdk.capture_message(message, level=level)
    except Exception:
        pass


@router.get("/health")
async def health():
    db_status = ping_db()
    return {"ok": True, "scope": "finance", "db": db_status}


# ===== Schemas =====
class LedgerBatchCreate(BaseModel):
    org_id: Optional[str] = None
    ts: Optional[str] = None
    source: Optional[str] = Field(None, description="orders/payouts/fees/adjustment")
    external_ref: Optional[str] = None
    memo: Optional[str] = None


class LedgerEntryCreate(BaseModel):
    entry_batch_id: int
    org_id: Optional[str] = None
    account_id: int
    ts: Optional[str] = None
    amount: float
    currency: Optional[str] = None
    debit: bool
    ref_type: Optional[str] = None
    ref_id: Optional[str] = None
    memo: Optional[str] = None


class SupplierInvoiceCreate(BaseModel):
    org_id: Optional[str] = None
    supplier_id: int
    invoice_no: str
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    currency: Optional[str] = None
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    status: str = "open"


class ReconTaskCreate(BaseModel):
    org_id: Optional[str] = None
    scope: str


# ===== Ledger =====
@router.get("/ledger/batches")
async def list_ledger_batches(
    org_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.ensure_scope(org_id, req_brain_ids=[])
    q = db.query(LedgerBatch)
    if org_id:
        q = q.filter(LedgerBatch.org_id == org_id)
    items = (
        q.order_by(LedgerBatch.id.desc())
        .offset(max(0, offset))
        .limit(max(1, min(limit, 500)))
        .all()
    )
    return {
        "items": [
            {
                "id": i.id,
                "org_id": i.org_id,
                "ts": i.ts,
                "source": i.source,
                "external_ref": i.external_ref,
                "memo": i.memo,
                "posted": i.posted,
                "created_at": getattr(i, "created_at", None),
            }
            for i in items
        ],
        "total": len(items),
    }


@router.post("/ledger/batches", status_code=status.HTTP_201_CREATED)
async def create_ledger_batch(
    payload: LedgerBatchCreate,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.require_role(["admin", "finance", "editor"])
    scope.ensure_scope(payload.org_id, req_brain_ids=[])
    obj = LedgerBatch(
        org_id=payload.org_id,
        ts=payload.ts,
        source=payload.source,
        external_ref=payload.external_ref,
        memo=payload.memo,
        posted=False,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    _sentry_breadcrumb(
        level="info",
        category="finance.ledger.batch",
        message="Ledger batch created",
        data={"id": obj.id, "org_id": obj.org_id, "source": obj.source},
    )
    return {"id": obj.id}


@router.get("/ledger/entries")
async def list_ledger_entries(
    org_id: Optional[str] = None,
    entry_batch_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.ensure_scope(org_id, req_brain_ids=[])
    q = db.query(LedgerEntry)
    if org_id:
        q = q.filter(LedgerEntry.org_id == org_id)
    if entry_batch_id:
        q = q.filter(LedgerEntry.entry_batch_id == entry_batch_id)
    items = (
        q.order_by(LedgerEntry.id.desc())
        .offset(max(0, offset))
        .limit(max(1, min(limit, 500)))
        .all()
    )
    return {
        "items": [
            {
                "id": i.id,
                "entry_batch_id": i.entry_batch_id,
                "org_id": i.org_id,
                "account_id": i.account_id,
                "ts": i.ts,
                "amount": i.amount,
                "currency": i.currency,
                "debit": i.debit,
                "ref_type": i.ref_type,
                "ref_id": i.ref_id,
                "memo": i.memo,
            }
            for i in items
        ],
        "total": len(items),
    }


@router.post("/ledger/entries", status_code=status.HTTP_201_CREATED)
async def create_ledger_entry(
    payload: LedgerEntryCreate,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.require_role(["admin", "finance", "editor"])
    scope.ensure_scope(payload.org_id, req_brain_ids=[])
    obj = LedgerEntry(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    _sentry_breadcrumb(
        level="info",
        category="finance.ledger.entry",
        message="Ledger entry created",
        data={"id": obj.id, "batch": obj.entry_batch_id, "account": obj.account_id, "debit": obj.debit},
    )
    return {"id": obj.id}


# ===== Supplier Invoices =====
@router.get("/invoices")
async def list_invoices(
    org_id: Optional[str] = None,
    supplier_id: Optional[int] = None,
    status_eq: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.ensure_scope(org_id, req_brain_ids=[])
    q = db.query(SupplierInvoice)
    if org_id:
        q = q.filter(SupplierInvoice.org_id == org_id)
    if supplier_id:
        q = q.filter(SupplierInvoice.supplier_id == supplier_id)
    if status_eq:
        q = q.filter(SupplierInvoice.status == status_eq)
    items = (
        q.order_by(SupplierInvoice.id.desc())
        .offset(max(0, offset))
        .limit(max(1, min(limit, 500)))
        .all()
    )
    return {
        "items": [
            {
                "id": i.id,
                "org_id": i.org_id,
                "supplier_id": i.supplier_id,
                "invoice_no": i.invoice_no,
                "invoice_date": i.invoice_date,
                "due_date": i.due_date,
                "currency": i.currency,
                "subtotal": i.subtotal,
                "tax": i.tax,
                "total": i.total,
                "status": i.status,
            }
            for i in items
        ],
        "total": len(items),
    }


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: SupplierInvoiceCreate,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.require_role(["admin", "finance", "editor"])
    scope.ensure_scope(payload.org_id, req_brain_ids=[])
    if abs((payload.subtotal + payload.tax) - payload.total) > 1e-6:
        raise HTTPException(status_code=400, detail="subtotal + tax must equal total")
    obj = SupplierInvoice(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    _sentry_breadcrumb(
        level="info",
        category="finance.invoices",
        message="Supplier invoice created",
        data={"id": obj.id, "supplier_id": obj.supplier_id, "total": obj.total, "status": obj.status},
    )
    return {"id": obj.id}


# ===== Reconciliation =====
@router.post("/recon/tasks", status_code=status.HTTP_201_CREATED)
async def create_recon_task(
    payload: ReconTaskCreate,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
    background_tasks: BackgroundTasks = None,
):
    scope.require_role(["admin", "finance", "editor"])
    scope.ensure_scope(payload.org_id, req_brain_ids=[])
    obj = ReconciliationTask(org_id=payload.org_id, scope=payload.scope, status="pending")
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # Schedule background processing to complete the task (dev-friendly)
    if background_tasks is not None:
        background_tasks.add_task(_process_recon_task, obj.id)
    _sentry_breadcrumb(
        level="info",
        category="finance.recon",
        message="Reconciliation task created",
        data={"id": obj.id, "org_id": obj.org_id, "scope": obj.scope},
    )
    return {"id": obj.id, "status": obj.status}


@router.get("/recon/tasks/{task_id}")
async def get_recon_task(
    task_id: int,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    obj = db.query(ReconciliationTask).filter(ReconciliationTask.id == task_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="task not found")
    scope.ensure_scope(obj.org_id, req_brain_ids=[])
    return {
        "id": obj.id,
        "org_id": obj.org_id,
        "scope": obj.scope,
        "status": obj.status,
        "started_at": obj.started_at,
        "finished_at": obj.finished_at,
        "stats": obj.stats,
    }


def _process_recon_task(task_id: int) -> None:
    """Background processor to complete reconciliation tasks.

    This is a lightweight dev implementation that marks the task as success
    and sets simple stats. In production, this should be replaced by a
    Celery/worker job that performs actual reconciliation.
    """
    SessionFactory = get_session_factory()
    db = SessionFactory()
    try:
        obj = db.query(ReconciliationTask).filter(ReconciliationTask.id == task_id).first()
        if not obj:
            return
        if not obj.started_at:
            obj.started_at = datetime.utcnow()
        # Simulate some processing
        obj.status = "success"
        obj.finished_at = datetime.utcnow()
        obj.stats = {"matched": 0, "unmatched": 0}
        db.add(obj)
        db.commit()
        _sentry_breadcrumb(
            level="info",
            category="finance.recon",
            message="Reconciliation task completed",
            data={"id": obj.id, "status": obj.status},
        )
    except Exception:
        db.rollback()
    finally:
        db.close()


# ===== Forecast =====
@router.get("/forecast")
async def get_forecast(
    org_id: Optional[str] = None,
    db: Session = Depends(get_db),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    scope.ensure_scope(org_id, req_brain_ids=[])
    q = db.query(CashFlowForecast)
    if org_id:
        q = q.filter(CashFlowForecast.org_id == org_id)
    items = q.order_by(CashFlowForecast.period_start.desc()).limit(120).all()
    return {
        "items": [
            {
                "id": i.id,
                "org_id": i.org_id,
                "period_start": i.period_start,
                "period_end": i.period_end,
                "inflow": i.inflow,
                "outflow": i.outflow,
                "net": i.net,
                "assumptions": i.assumptions,
            }
            for i in items
        ],
        "total": len(items),
    }
