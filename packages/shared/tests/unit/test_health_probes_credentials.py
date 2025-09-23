import importlib
import os
import sys
import types

import pytest


@pytest.fixture(autouse=True)
def clear_settings_cache():
    # Ensure settings are reloaded fresh for each test case
    from packages.shared.config import loader

    loader.get_settings.cache_clear()
    yield
    loader.get_settings.cache_clear()


def set_env(env: dict[str, str]):
    # Helper to set env vars for a test
    for k in list(os.environ.keys()):
        if k in env or k.startswith("CJ_") or k.startswith("GSHEETS_") or k.startswith("S3_") or k in {
            "GOOGLE_APPLICATION_CREDENTIALS"
        }:
            # Remove conflicting keys to get deterministic behavior
            if k not in env:
                os.environ.pop(k, None)
    for k, v in env.items():
        os.environ[k] = v


def test_cj_disabled_when_no_key(monkeypatch):
    set_env({})
    # Reload health module after env mutation
    probes = importlib.import_module("packages.shared.health.probes")
    checker = probes.HealthChecker()
    res = checker.check_cj()
    assert res.status is True
    assert res.details and res.details.get("enabled") is False


def test_cj_enabled_with_key_and_adapter_stub(monkeypatch):
    set_env({"CJ_API_KEY": "test-key"})
    # Provide a stub CJAdapter module before probe imports it
    dummy = types.SimpleNamespace()

    class CJAdapter:  # noqa: N801 (test stub)
        def __init__(self):
            pass

        def fetch_products(self, limit: int = 1):
            return {"ok": True, "limit": limit}

    dummy.CJAdapter = CJAdapter
    sys.modules["packages.shared.adapters.cj"] = dummy

    probes = importlib.import_module("packages.shared.health.probes")
    checker = probes.HealthChecker()
    res = checker.check_cj()
    assert res.status is True
    assert "CJ API connection successful" in res.message


def test_s3_disabled_without_keys(monkeypatch):
    set_env({
        "S3_BUCKET": "bucket",
        "S3_REGION": "us-east-1",
        # intentionally omit S3_ACCESS_KEY_ID / S3_SECRET_ACCESS_KEY
    })
    probes = importlib.import_module("packages.shared.health.probes")
    checker = probes.HealthChecker()
    res = checker.check_s3()
    assert res.status is True
    assert res.details and res.details.get("enabled") is False


def test_s3_ok_with_keys_and_boto3_stub(monkeypatch):
    set_env({
        "S3_BUCKET": "bucket",
        "S3_REGION": "us-east-1",
        "S3_ACCESS_KEY_ID": "AKIA...",
        "S3_SECRET_ACCESS_KEY": "secret",
    })

    class DummyS3:
        def head_bucket(self, Bucket: str):  # noqa: N803
            return {"ok": True, "bucket": Bucket}

    class DummyBoto3Module:
        def client(self, name, **kwargs):
            assert name == "s3"
            return DummyS3()

    # Install stub modules
    sys.modules["boto3"] = DummyBoto3Module()  # type: ignore
    exc_mod = types.SimpleNamespace(ClientError=Exception)
    # Provide both parent package and submodule for import machinery
    sys.modules["botocore"] = types.SimpleNamespace(exceptions=exc_mod)  # type: ignore
    sys.modules["botocore.exceptions"] = exc_mod  # type: ignore

    probes = importlib.import_module("packages.shared.health.probes")
    checker = probes.HealthChecker()
    res = checker.check_s3()
    assert res.status is True
    assert res.details and res.details.get("bucket") == "bucket"


def test_sheets_disabled_without_creds_or_ledger_id(monkeypatch):
    set_env({})
    os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    os.environ.pop("GSHEETS_LEDGER_ID", None)

    probes = importlib.import_module("packages.shared.health.probes")
    checker = probes.HealthChecker()
    res = checker.check_sheets()
    assert res.status is True
    assert res.details and res.details.get("enabled") is False


def test_sheets_ok_with_ledger_id_and_stub_client(monkeypatch):
    set_env({"GSHEETS_LEDGER_ID": "sheet-123"})

    class SheetsClient:
        def health_check(self):
            return {"ok": True, "latency_ms": 12, "spreadsheet_id": "sheet-123"}

    # Provide stub module
    sheets_mod = types.SimpleNamespace(SheetsClient=SheetsClient)
    sys.modules["packages.shared.sheets"] = sheets_mod

    probes = importlib.import_module("packages.shared.health.probes")
    checker = probes.HealthChecker()
    res = checker.check_sheets()
    assert res.status is True
    assert res.details and res.details.get("spreadsheet_id") == "sheet-123"
