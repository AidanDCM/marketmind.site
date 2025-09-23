from fastapi.testclient import TestClient

from apps.hive_api.main import app

client = TestClient(app)


def test_finance_health():
    r = client.get("/finance/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True


def test_finance_ledger_entries_list():
    r = client.get("/finance/ledger/entries")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body


def test_finance_ledger_batches_list():
    r = client.get("/finance/ledger/batches")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body


def test_finance_invoices_list():
    r = client.get("/finance/invoices")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body


def test_finance_forecast_list():
    r = client.get("/finance/forecast")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body
