from contextlib import contextmanager

from fastapi.testclient import TestClient

from apps.hive_api.main import app
from apps.hive_api.security import SubjectScope, get_subject_scope_optional


@contextmanager
def finance_scope_override(org_id: str = "org_demo"):
    def _override():
        return SubjectScope(sub="test", role="finance", org_id=org_id, brain_ids=["*"])

    app.dependency_overrides[get_subject_scope_optional] = _override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_subject_scope_optional, None)


def test_create_ledger_batch_and_entry():
    client = TestClient(app)
    with finance_scope_override():
        # Create a batch
        r = client.post(
            "/finance/ledger/batches",
            json={
                "org_id": "org_demo",
                "ts": "2025-01-01T00:00:00Z",
                "source": "orders",
                "external_ref": "batch-smoke",
                "memo": "smoke batch",
            },
        )
        assert r.status_code == 201, r.text
        batch_id = r.json()["id"]

        # Create an entry under the batch
        r = client.post(
            "/finance/ledger/entries",
            json={
                "entry_batch_id": batch_id,
                "org_id": "org_demo",
                "account_id": 1001,
                "ts": "2025-01-01T00:00:00Z",
                "amount": 123.45,
                "currency": "USD",
                "debit": True,
                "ref_type": "order",
                "ref_id": "ord-1",
                "memo": "smoke entry",
            },
        )
        assert r.status_code == 201, r.text
        entry_id = r.json()["id"]
        assert isinstance(entry_id, int)

        # List entries scoped to org
        r = client.get(
            "/finance/ledger/entries", params={"org_id": "org_demo", "entry_batch_id": batch_id}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1


def test_create_invoice_and_validation():
    client = TestClient(app)
    with finance_scope_override():
        # Validation error when totals mismatch
        r = client.post(
            "/finance/invoices",
            json={
                "org_id": "org_demo",
                "supplier_id": 1,
                "invoice_no": "INV-1",
                "subtotal": 10.0,
                "tax": 1.0,
                "total": 11.1,
            },
        )
        assert r.status_code == 400

        # Happy path
        r = client.post(
            "/finance/invoices",
            json={
                "org_id": "org_demo",
                "supplier_id": 1,
                "invoice_no": "INV-2",
                "subtotal": 10.0,
                "tax": 1.0,
                "total": 11.0,
                "currency": "USD",
            },
        )
        assert r.status_code == 201, r.text
        inv_id = r.json()["id"]
        assert isinstance(inv_id, int)

        # List invoices
        r = client.get("/finance/invoices", params={"org_id": "org_demo"})
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1


def test_recon_task_create_and_fetch():
    client = TestClient(app)
    with finance_scope_override():
        r = client.post(
            "/finance/recon/tasks",
            json={
                "org_id": "org_demo",
                "scope": "orders",
            },
        )
        assert r.status_code == 201, r.text
        tid = r.json()["id"]

        r = client.get(f"/finance/recon/tasks/{tid}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == tid
        assert data["status"] in ("pending", "running", "success", "failed")
