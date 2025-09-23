from fastapi.testclient import TestClient

from apps.hive_api.main import app

client = TestClient(app)


def test_profit_log_exists_and_is_list():
    r = client.get("/profit/log")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict)
    assert "items" in body and isinstance(body["items"], list)
    assert "total" in body and "limit" in body and "offset" in body


def test_profit_log_limit_param_caps_results():
    r = client.get("/profit/log?limit=1")
    assert r.status_code == 200
    body = r.json()
    assert body.get("limit") == 1
    # If any seed rows exist, items length should be <= limit
    assert len(body.get("items", [])) <= 1
