import logging
import time
from datetime import datetime
from typing import Literal, Optional

from sqlalchemy import select

from apps.hive_worker.celery_app import app
from packages.shared.adapters.base import ProductIngestItem
from packages.shared.adapters.cj import CJAdapter
from packages.shared.config.flags import is_module_enabled, is_simulation
from packages.shared.db import get_db
from packages.shared.models_db import (
    Competitor,
    IngestCheckpoint,
    PriceHistory,
    Product,
    SupplierOffer,
)


def _upsert_sample(session):
    # Sample data to validate pipeline end-to-end
    sample = {
        "sku": "SAMPLE-001",
        "asin": "B000TEST01",
        "title": "Sample Pet Toy",
        "brand": "MarketMind",
        "image": "https://picsum.photos/seed/marketmind/600/600",
        "supplier": {
            "name": "cj",
            "supplier_sku": "CJ-XYZ-001",
            "cost": 8.50,
            "stock": 120,
            "lead": 48,
            "ships_from": "US-CA",
        },
        "competitor": {
            "channel": "amazon",
            "price": 19.99,
            "seller": "SampleSeller",
        },
    }

    # Product
    existing = session.execute(
        select(Product).where(Product.sku == sample["sku"])
    ).scalar_one_or_none()
    if existing is None:
        p = Product(
            sku=sample["sku"],
            asin=sample["asin"],
            title=sample["title"],
            brand=sample["brand"],
            images={"main": sample["image"]},
        )
        session.add(p)
        session.flush()
    else:
        p = existing
        p.title = sample["title"]
        p.brand = sample["brand"]
        p.images = {"main": sample["image"]}

    # Supplier offer
    offer = session.execute(
        select(SupplierOffer).where(
            SupplierOffer.product_id == p.id,
            SupplierOffer.supplier_name == sample["supplier"]["name"],
            SupplierOffer.supplier_sku == sample["supplier"]["supplier_sku"],
        )
    ).scalar_one_or_none()
    if offer is None:
        offer = SupplierOffer(
            product_id=p.id,
            supplier_name=sample["supplier"]["name"],
            supplier_sku=sample["supplier"]["supplier_sku"],
            cost=sample["supplier"]["cost"],
            stock_qty=sample["supplier"]["stock"],
            lead_time_hours=sample["supplier"]["lead"],
            ships_from=sample["supplier"]["ships_from"],
        )
        session.add(offer)
    else:
        offer.cost = sample["supplier"]["cost"]
        offer.stock_qty = sample["supplier"]["stock"]
        offer.lead_time_hours = sample["supplier"]["lead"]
        offer.ships_from = sample["supplier"]["ships_from"]

    # Competitor snapshot
    comp = Competitor(
        product_id=p.id,
        channel=sample["competitor"]["channel"],
        asin=sample["asin"],
        seller=sample["competitor"]["seller"],
        price=sample["competitor"]["price"],
    )
    session.add(comp)

    # Price history point
    ph = PriceHistory(
        product_id=p.id,
        channel=sample["competitor"]["channel"],
        price=sample["competitor"]["price"],
        source="competitor",
    )
    session.add(ph)


def _write_checkpoint(
    session,
    *,
    org_id: Optional[str],
    brain_id: Optional[str],
    pipeline: str,
    source: str,
    key: Optional[str],
    value: Optional[str],
):
    logger = logging.getLogger(__name__)
    existing = session.execute(
        select(IngestCheckpoint).where(
            IngestCheckpoint.org_id == org_id,
            IngestCheckpoint.brain_id == brain_id,
            IngestCheckpoint.pipeline == pipeline,
            IngestCheckpoint.source == source,
            IngestCheckpoint.key == key,
        )
    ).scalar_one_or_none()
    if existing is None:
        cp = IngestCheckpoint(
            org_id=org_id,
            brain_id=brain_id,
            pipeline=pipeline,
            source=source,
            key=key,
            value=value,
        )
        session.add(cp)
        logger.info(
            "checkpoint.created",
            extra={
                "pipeline": pipeline,
                "source": source,
                "key": key,
                "value": value,
                "org_id": org_id,
                "brain_id": brain_id,
            },
        )
    else:
        existing.value = value
        logger.info(
            "checkpoint.updated",
            extra={
                "pipeline": pipeline,
                "source": source,
                "key": key,
                "value": value,
                "org_id": org_id,
                "brain_id": brain_id,
            },
        )


@app.task(
    bind=True,
    queue="q.catalog", 
    name="apps.hive_worker.tasks.ingest.catalog_sync",
    acks_late=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,)
)
def catalog_sync(self, org_id: str, brain_id: str, supplier: Literal["cj"] = "cj", full: bool = False):
    logger = logging.getLogger(__name__)
    _t0 = time.monotonic()
    logger.info(
        "task.start",
        extra={
            "task": "catalog_sync",
            "supplier": supplier,
            "full": full,
            "org_id": org_id,
            "brain_id": brain_id,
        },
    )
    # Idempotent supplier catalog sync; current support: CJ
    items: list[ProductIngestItem] = []
    if supplier == "cj":
        try:
            cj = CJAdapter()
            items = cj.fetch_products(limit=200)
        except Exception as e:
            logger.warning("catalog.cj_fetch_failed", extra={"error": str(e)})
            items = []
    for session in get_db():
        for it in items:
            _upsert_from_item(session, it)
        _write_checkpoint(
            session,
            org_id=org_id,
            brain_id=brain_id,
            pipeline="catalog",
            source=supplier,
            key=None,
            value=datetime.utcnow().isoformat(),
        )
        session.commit()
        logger.info(
            "task.end",
            extra={
                "task": "catalog_sync",
                "supplier": supplier,
                "full": full,
                "org_id": org_id,
                "brain_id": brain_id,
            },
        )
        break


@app.task(
    bind=True,
    queue="q.signals", 
    name="apps.hive_worker.tasks.ingest.signals_snapshot",
    acks_late=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,)
)
def signals_snapshot(
    self,
    org_id: str,
    brain_id: str,
    channel: Literal["amazon", "ebay"] = "amazon",
    asin_bucket: Optional[int] = None,
):
    logger = logging.getLogger(__name__)
    _t0 = time.monotonic()
    logger.info(
        "task.start",
        extra={
            "task": "signals_snapshot",
            "channel": channel,
            "asin_bucket": asin_bucket,
            "org_id": org_id,
            "brain_id": brain_id,
        },
    )
    for session in get_db():
        _write_checkpoint(
            session,
            org_id=org_id,
            brain_id=brain_id,
            pipeline="signals",
            source=channel,
            key=str(asin_bucket) if asin_bucket is not None else None,
            value=datetime.utcnow().isoformat(),
        )
        session.commit()
        logger.info(
            "task.end",
            extra={
                "task": "signals_snapshot",
                "channel": channel,
                "asin_bucket": asin_bucket,
                "org_id": org_id,
                "brain_id": brain_id,
            },
        )
        break


@app.task(queue="q.orders", name="apps.hive_worker.tasks.ingest.orders_pull")
def orders_pull(
    org_id: str,
    brain_id: str,
    channel: Literal["amazon", "ebay"] = "amazon",
    since_iso: Optional[str] = None,
):
    logger = logging.getLogger(__name__)
    if not is_module_enabled("orders"):
        logger.info("task.skip", extra={"task": "orders_pull", "reason": "orders_disabled"})
        return {"status": "skipped", "reason": "orders_disabled"}
    for session in get_db():
        _write_checkpoint(
            session,
            org_id=org_id,
            brain_id=brain_id,
            pipeline="orders",
            source=channel,
            key=None,
            value=since_iso or datetime.utcnow().isoformat(),
        )
        session.commit()
        logger.info(
            "task.end",
            extra={
                "task": "orders_pull",
                "channel": channel,
                "since_iso": since_iso,
                "org_id": org_id,
                "brain_id": brain_id,
            },
        )
        break


@app.task(queue="q.backfill", name="apps.hive_worker.tasks.ingest.backfill_price_history")
def backfill_price_history(
    org_id: str,
    brain_id: str,
    channel: Literal["amazon", "ebay"],
    asins: list[str],
    start_iso: str,
    end_iso: str,
):
    logger = logging.getLogger(__name__)
    if not is_simulation():
        logger.info(
            "task.skip", extra={"task": "backfill_price_history", "reason": "not_simulation"}
        )
        return {"status": "skipped", "reason": "not_simulation"}
    scope_key = f"{channel}:{len(asins)}:{start_iso}->{end_iso}"
    for session in get_db():
        _write_checkpoint(
            session,
            org_id=org_id,
            brain_id=brain_id,
            pipeline="signals",
            source=channel,
            key=scope_key,
            value=end_iso,
        )
        session.commit()
        logger.info(
            "task.end",
            extra={
                "task": "backfill_price_history",
                "channel": channel,
                "asins_count": len(asins),
                "start_iso": start_iso,
                "end_iso": end_iso,
                "org_id": org_id,
                "brain_id": brain_id,
            },
        )
        break


def _upsert_from_item(session, item: ProductIngestItem):
    # Product
    existing = session.execute(select(Product).where(Product.sku == item.sku)).scalar_one_or_none()
    if existing is None:
        p = Product(
            sku=item.sku,
            asin=item.asin,
            title=item.title,
            brand=item.brand,
            images={"main": item.image} if item.image else None,
        )
        session.add(p)
        session.flush()
    else:
        p = existing
        p.title = item.title
        p.brand = item.brand
        p.images = {"main": item.image} if item.image else p.images

    # Supplier offer
    s = item.supplier
    # Unique constraint is on (supplier_name, supplier_sku),
    # so search using that pair and then (re)assign product_id.
    offer = session.execute(
        select(SupplierOffer).where(
            SupplierOffer.supplier_name == s.supplier_name,
            SupplierOffer.supplier_sku == s.supplier_sku,
        )
    ).scalar_one_or_none()
    if offer is None:
        offer = SupplierOffer(
            product_id=p.id,
            supplier_name=s.supplier_name,
            supplier_sku=s.supplier_sku,
            cost=s.cost,
            stock_qty=s.stock,
            lead_time_hours=s.lead_hours,
            ships_from=s.ships_from,
        )
        session.add(offer)
    else:
        offer.product_id = p.id
        offer.cost = s.cost
        offer.stock_qty = s.stock
        offer.lead_time_hours = s.lead_hours
        offer.ships_from = s.ships_from

    # Optional competitor and price history
    if item.competitor:
        c = item.competitor
        comp = Competitor(
            product_id=p.id,
            channel=c.channel,
            asin=c.asin or item.asin,
            seller=c.seller,
            price=c.price,
        )
        session.add(comp)

        ph = PriceHistory(
            product_id=p.id,
            channel=c.channel,
            price=c.price,
            source="competitor",
        )
        session.add(ph)


@app.task(
    bind=True,
    name="apps.hive_worker.tasks.ingest.run_ingest",
    acks_late=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,)
)
def run_ingest(self):
    # Prefer adapter path when possible; fallback to sample
    use_adapter = True  # enable stub even if CJ_API_KEY is not set
    items = []
    if use_adapter:
        try:
            cj = CJAdapter()
            # Allow override via env CJ_INGEST_LIMIT (default 200)
            import os as _os

            _limit = int(_os.getenv("CJ_INGEST_LIMIT", "200"))
            items = cj.fetch_products(limit=_limit)
        except Exception:
            # Adapter failed; will fallback to sample
            items = []

    for session in get_db():
        if items:
            for it in items:
                _upsert_from_item(session, it)
        else:
            _upsert_sample(session)
        session.commit()
        break
    print("Ingest completed: adapter_items=" + str(len(items)))
