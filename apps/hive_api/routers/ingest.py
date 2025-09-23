"""
Ingestion API endpoints for catalog sync, pricing snapshots, orders, and backfills.

These endpoints trigger Celery tasks and expose status via checkpoints.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, select

from apps.hive_worker.celery_app import app as celery_app
from packages.shared.config import get_settings, is_module_enabled, is_simulation
from packages.shared.db import get_db
from packages.shared.models_db import IngestCheckpoint
from packages.shared.sheets import get_ledger_writer
from packages.shared.spapi_client import SpapiClient

router = APIRouter(prefix="/ingest", tags=["ingestion"])


class CatalogSyncRequest(BaseModel):
    supplier: str = Field(..., description="Supplier name (e.g., 'cj')")
    org_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brain_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full: bool = Field(default=False, description="Full sync vs delta")


class PricingSnapshotRequest(BaseModel):
    asins: List[str] = Field(..., description="List of ASINs to snapshot")
    org_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brain_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    write_to_sheets: bool = Field(default=True, description="Write pricing decisions to sheets")


class OrderPullRequest(BaseModel):
    channel: str = Field(..., description="Channel name (e.g., 'amazon')")
    org_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brain_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    since_iso: Optional[str] = Field(default=None, description="Pull orders since this timestamp")


class SignalsSnapshotRequest(BaseModel):
    channel: str = Field("amazon", description="Channel for signals (pricing snapshot)")
    asin_bucket: Optional[int] = Field(default=None, description="Optional bucket id for sharding")
    org_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brain_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


@router.get("/status")
def get_ingestion_status():
    """Get status of ingestion pipelines via latest checkpoints."""
    # Aggregate last checkpoint per (pipeline, source)
    status = {}
    for session in get_db():
        rows = (
            session.execute(select(IngestCheckpoint).order_by(desc(IngestCheckpoint.updated_at)))
            .scalars()
            .all()
        )
        for cp in rows:
            key = (cp.pipeline, cp.source)
            if key not in status:
                status[key] = {
                    "org_id": cp.org_id,
                    "brain_id": cp.brain_id,
                    "pipeline": cp.pipeline,
                    "source": cp.source,
                    "key": cp.key,
                    "value": cp.value,
                    "updated_at": cp.updated_at.isoformat() if cp.updated_at else None,
                }
        break
    return {
        "flags": {
            "simulation_enabled": is_simulation(),
            "order_sync_enabled": is_module_enabled("orders"),
        },
        "checkpoints": list(status.values()),
    }


@router.post("/run/catalog")
def run_catalog_sync(request: CatalogSyncRequest):
    """Enqueue catalog synchronization for a supplier via Celery."""
    if request.supplier != "cj":
        raise HTTPException(status_code=400, detail=f"Unsupported supplier: {request.supplier}")
    try:
        task = celery_app.send_task(
            "apps.hive_worker.tasks.ingest.catalog_sync",
            args=[request.org_id, request.brain_id, request.supplier, request.full],
            queue="q.catalog",
        )
        return {"status": "queued", "task_id": task.id}
    except Exception as e:  # broker/backend may be unavailable in dev
        # Non-fatal in dev/CI: allow verification to proceed without a worker
        print(f"[ingest] catalog_sync enqueue failed: {e}")
        return {
            "status": "skipped",
            "reason": "celery_unavailable",
            "org_id": request.org_id,
            "brain_id": request.brain_id,
            "supplier": request.supplier,
            "full": request.full,
        }


@router.post("/run/pricing")
def run_pricing_snapshot(request: PricingSnapshotRequest, background_tasks: BackgroundTasks):
    """Trigger pricing snapshot for specified ASINs."""
    settings = get_settings()

    if not getattr(settings.amazon, "client_id", None):
        # In unconfigured environments, return a graceful 200 with skip reason
        return {
            "status": "skipped",
            "reason": "spapi_not_configured",
            "asins_count": len(request.asins),
            "write_to_sheets": request.write_to_sheets,
            "org_id": request.org_id,
            "brain_id": request.brain_id,
        }

    def pricing_task():
        try:
            client = SpapiClient(
                client_id=settings.amazon.client_id,
                client_secret=settings.amazon.client_secret,
                refresh_token=settings.amazon.refresh_token,
                region=settings.amazon.region,
            )

            # Get competitive pricing
            pricing_data = client.get_competitive_pricing(request.asins)

            # Process each ASIN
            results = []
            for asin in request.asins:
                best_price = client.extract_best_price(pricing_data, asin)
                buybox_flag = client.extract_buybox_flag(pricing_data, asin)

                result = {
                    "asin": asin,
                    "comp_best_price": best_price,
                    "buybox": buybox_flag,
                    "recorded_at": datetime.utcnow().isoformat(),
                }
                results.append(result)

                # Write to sheets if requested
                if request.write_to_sheets and best_price:
                    ledger = get_ledger_writer()
                    ledger.write_pricing_decision(
                        {
                            "asin_sku": asin,
                            "comp_best_price": best_price,
                            "proposed_price": 0.0,  # No proposal yet
                            "reason": "competitive_snapshot",
                            "sim_live": "live" if not is_simulation() else "simulation",
                        }
                    )

            print(f"Pricing snapshot completed: {len(results)} ASINs processed")

            # Write a minimal ingestion checkpoint for visibility in /ingest/status
            try:
                now_iso = datetime.utcnow().isoformat()
                for session in get_db():
                    existing = session.execute(
                        select(IngestCheckpoint).where(
                            IngestCheckpoint.org_id == request.org_id,
                            IngestCheckpoint.brain_id == request.brain_id,
                            IngestCheckpoint.pipeline == "pricing",
                            IngestCheckpoint.source == "amazon",
                            IngestCheckpoint.key == "last_snapshot_iso",
                        )
                    ).scalar_one_or_none()
                    if existing is None:
                        session.add(
                            IngestCheckpoint(
                                org_id=request.org_id,
                                brain_id=request.brain_id,
                                pipeline="pricing",
                                source="amazon",
                                key="last_snapshot_iso",
                                value=now_iso,
                            )
                        )
                    else:
                        existing.value = now_iso
                    session.commit()
                    break
            except Exception:
                # Non-fatal: checkpoint is an observability enhancement only
                pass

        except Exception as e:
            print(f"Pricing snapshot failed: {e}")

    background_tasks.add_task(pricing_task)

    return {
        "status": "started",
        "asins_count": len(request.asins),
        "write_to_sheets": request.write_to_sheets,
        "org_id": request.org_id,
        "brain_id": request.brain_id,
    }


@router.post("/run/orders")
def run_order_pull(request: OrderPullRequest):
    """Enqueue order pull via Celery."""
    if not is_module_enabled("orders"):
        # Gracefully skip in environments where orders module is disabled
        return {
            "status": "skipped",
            "reason": "orders_disabled",
            "channel": request.channel,
            "org_id": request.org_id,
            "brain_id": request.brain_id,
        }
    if request.channel not in ("amazon", "ebay"):
        raise HTTPException(status_code=400, detail=f"Unsupported channel: {request.channel}")
    try:
        task = celery_app.send_task(
            "apps.hive_worker.tasks.ingest.orders_pull",
            args=[request.org_id, request.brain_id, request.channel, request.since_iso],
            queue="q.orders",
        )
        return {"status": "queued", "task_id": task.id}
    except Exception as e:
        # Broker/backend may be unavailable in dev/CI
        print(f"[ingest] orders_pull enqueue failed: {e}")
        return {
            "status": "skipped",
            "reason": "celery_unavailable",
            "channel": request.channel,
            "org_id": request.org_id,
            "brain_id": request.brain_id,
            "since_iso": request.since_iso,
        }


@router.post("/run/signals")
def run_signals_snapshot(request: SignalsSnapshotRequest):
    """Enqueue signals snapshot (competitive pricing) via Celery."""
    if request.channel not in ("amazon", "ebay"):
        raise HTTPException(status_code=400, detail=f"Unsupported channel: {request.channel}")
    task = celery_app.send_task(
        "apps.hive_worker.tasks.ingest.signals_snapshot",
        args=[request.org_id, request.brain_id, request.channel, request.asin_bucket],
        queue="q.signals",
    )
    return {"status": "queued", "task_id": task.id}


class BackfillPriceHistoryRequest(BaseModel):
    channel: str
    asins: List[str]
    start_iso: str
    end_iso: str
    org_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brain_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


@router.post("/backfill/price_history")
def backfill_price_history(request: BackfillPriceHistoryRequest):
    """Backfill price history for ASINs over a date range via Celery."""
    if not is_simulation():
        raise HTTPException(
            status_code=400, detail="Backfill requires SIMULATION_ENABLED=true for safety"
        )
    if request.channel not in ("amazon", "ebay"):
        raise HTTPException(status_code=400, detail=f"Unsupported channel: {request.channel}")
    task = celery_app.send_task(
        "apps.hive_worker.tasks.ingest.backfill_price_history",
        args=[
            request.org_id,
            request.brain_id,
            request.channel,
            request.asins,
            request.start_iso,
            request.end_iso,
        ],
        queue="q.backfill",
    )
    return {"status": "queued", "task_id": task.id}


class ReplayCheckpointRequest(BaseModel):
    org_id: Optional[str] = None
    brain_id: Optional[str] = None
    pipeline: str
    source: str
    key: Optional[str] = None
    value: Optional[str] = None


@router.post("/replay/checkpoint")
def set_checkpoint(request: ReplayCheckpointRequest):
    """Manually set a checkpoint value to control replay/watermarks."""
    for session in get_db():
        existing = session.execute(
            select(IngestCheckpoint).where(
                IngestCheckpoint.org_id == request.org_id,
                IngestCheckpoint.brain_id == request.brain_id,
                IngestCheckpoint.pipeline == request.pipeline,
                IngestCheckpoint.source == request.source,
                IngestCheckpoint.key == request.key,
            )
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                IngestCheckpoint(
                    org_id=request.org_id,
                    brain_id=request.brain_id,
                    pipeline=request.pipeline,
                    source=request.source,
                    key=request.key,
                    value=request.value,
                )
            )
        else:
            existing.value = request.value
        session.commit()
        break
    return {"status": "ok"}


@router.get("/health")
def ingestion_health():
    """Health check for ingestion services."""
    # Keep CJ supplier section non-fatal and config-agnostic
    cj_health = {"ok": False, "error": "not_configured"}

    settings = get_settings()
    # Amazon config access may throw if structure differs; guard it
    try:
        amazon_configured = bool(getattr(settings.amazon, "client_id", None))
        amazon_mode = getattr(settings.amazon, "mode", None)
    except Exception:
        amazon_configured = False
        amazon_mode = None

    # This flag is not part of the current schema; default to False
    inventory_flag = False

    return {
        "suppliers": {"cj": cj_health},
        "channels": {"amazon": {"configured": amazon_configured, "mode": amazon_mode}},
        "flags": {
            "simulation_enabled": is_simulation(),
            "order_sync_enabled": is_module_enabled("orders"),
            "inventory_sync_enabled": inventory_flag,
        },
    }
