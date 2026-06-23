"""Tests for marketmind.order_lifecycle."""

import json

from marketmind.db.engine import make_engine
from marketmind.db.models import Base, ImportBatchRow
from marketmind.order_lifecycle import build_order_lifecycle, classify_order_stage


def test_classify_stripe_paid():
    stage, raw = classify_order_stage("stripe_charges", {"status": "succeeded"})
    assert stage == "paid"
    assert raw == "succeeded"


def test_classify_refunded():
    stage, _ = classify_order_stage("stripe_webhook", {"event_type": "charge.refunded"})
    assert stage == "refunded"


def test_build_from_import_batches():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    from sqlalchemy.orm import Session

    rows = [{"id": "ord_1", "status": "paid", "amount": "5900", "currency": "usd"}]
    with Session(engine) as session:
        session.add(ImportBatchRow(
            source="stripe_charges",
            total_rows=1,
            ok_count=1,
            rows_json=json.dumps(rows),
        ))
        session.commit()

    entries = build_order_lifecycle(engine)
    assert len(entries) == 1
    assert entries[0].order_id == "ord_1"
    assert entries[0].stage == "paid"
