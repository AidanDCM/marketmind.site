from __future__ import annotations

import json

from packages.services.governance import ContractMonitor, SchemaRecord
from packages.database.models.governance import APIContract, RiskEvent


def test_contract_monitor_no_drift_then_drift(db_session):
    cm = ContractMonitor()

    base_schema = {"fields": ["id", "price"], "version": 1}
    rec1 = SchemaRecord(org_id="org1", provider="amazon", version="v1", schema=base_schema)

    # First record: establishes baseline, should NOT create a risk_event
    row1 = cm.record(db_session, rec1)

    api_rows = db_session.query(APIContract).all()
    assert len(api_rows) == 1
    assert api_rows[0].schema_hash == ContractMonitor.compute_hash(base_schema)

    risk_rows = db_session.query(RiskEvent).all()
    assert len(risk_rows) == 0

    # Change schema -> drift expected (risk_event)
    changed_schema = {"fields": ["id", "price", "currency"], "version": 1}
    rec2 = SchemaRecord(org_id="org1", provider="amazon", version="v1", schema=changed_schema)

    row2 = cm.record(db_session, rec2)

    api_rows = db_session.query(APIContract).order_by(APIContract.id.asc()).all()
    assert len(api_rows) == 2
    assert api_rows[1].schema_hash == ContractMonitor.compute_hash(changed_schema)

    risk_rows = db_session.query(RiskEvent).all()
    assert len(risk_rows) == 1
    r = risk_rows[0]
    assert r.signal == "schema_drift"
    assert r.level == "high"
    meta = json.loads(r.meta)
    assert meta["prev_hash"] == api_rows[0].schema_hash
    assert meta["new_hash"] == api_rows[1].schema_hash
