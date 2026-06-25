"""Phase B pass 19 (rotation 3): commerce adapters contract parity and deeper coverage."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.approval_gate_contract import EXECUTOR_HANDLER_ACTIONS, HIGH_RISK_ACTIONS
from marketmind.commerce_adapters_contract import (
    CHECK_COMMERCE_CONFIG_CLI,
    COMMERCE_ACTION_ALIASES,
    COMMERCE_API_EXECUTE_PATHS,
    COMMERCE_API_READ_PATHS,
    COMMERCE_DRY_RUN_FLAGS,
    COMMERCE_HANDLER_ACTIONS,
    COMMERCE_IMPORT_API_PATHS,
    COMMERCE_LIVE_WRITES_FLAG,
    COMMERCE_SOURCE_API_PATHS,
    DESKTOP_API_CLIENT_PATH,
    GMAIL_INTEGRATION_KEYS,
    INTEGRATIONS_SECRET_LEAK_MARKERS,
)
from marketmind.commerce_approval_policy import normalize_commerce_action
from marketmind.db import approval_store
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.docs_contract import REPO_ROOT
from marketmind.executor import _HANDLERS, record_action_payload
from marketmind.logging_config import mask_secret
from marketmind.schemas import (
    ApprovalRecord,
    ApprovalStatus,
    ProductDraftPayload,
    RiskLevel,
    ShopifyVariant,
)

_STRIPE_KEY = "sk_test_CONTRACT_SECRET_STRIPE_999"
_SHOPIFY_TOKEN = "shpat_CONTRACT_SECRET_SHOPIFY_999"
_GMAIL_SECRET = "gmail_client_secret_CONTRACT_999"
_GMAIL_REFRESH = "refresh_token_CONTRACT_abc123"


def _assert_no_secrets(text: str) -> None:
    for secret in (_STRIPE_KEY, _SHOPIFY_TOKEN, _GMAIL_SECRET, _GMAIL_REFRESH):
        assert secret not in text, f"Secret leaked into output: {secret[:8]}..."


@pytest.fixture
def commerce_contract_engine():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def commerce_contract_client(commerce_contract_engine):
    app.state.engine = commerce_contract_engine
    with TestClient(app) as client:
        yield client
    app.state.engine = None


@pytest.mark.parametrize(
    "sample",
    [
        f"prefix {marker}SAMPLE_TAIL suffix"
        for marker in INTEGRATIONS_SECRET_LEAK_MARKERS
    ],
    ids=[m.strip().replace(" ", "_") for m in INTEGRATIONS_SECRET_LEAK_MARKERS],
)
def test_deploy_integrations_leak_markers_redacted_by_mask_secret(sample: str):
    masked = mask_secret(sample)
    for marker in INTEGRATIONS_SECRET_LEAK_MARKERS:
        if marker in sample:
            assert marker not in masked or "***REDACTED***" in masked


def test_commerce_handler_actions_match_executor_registry():
    assert COMMERCE_HANDLER_ACTIONS == EXECUTOR_HANDLER_ACTIONS
    assert COMMERCE_HANDLER_ACTIONS == frozenset(_HANDLERS)


@pytest.mark.parametrize("action", sorted(COMMERCE_HANDLER_ACTIONS))
def test_handler_actions_normalize_to_high_risk_policy(action: str):
    if action in COMMERCE_ACTION_ALIASES:
        assert normalize_commerce_action(action) in HIGH_RISK_ACTIONS
    else:
        assert action in HIGH_RISK_ACTIONS


def test_desktop_client_documents_commerce_api_paths():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    for path in (
        *COMMERCE_API_READ_PATHS,
        "/execute/",
        "/execute/log",
        *COMMERCE_SOURCE_API_PATHS,
        *COMMERCE_IMPORT_API_PATHS,
    ):
        assert path.replace("{approval_id}", "") in text or path in text


def test_check_commerce_config_cli_path_exists():
    cli = REPO_ROOT / CHECK_COMMERCE_CONFIG_CLI
    assert cli.is_file()
    source = cli.read_text(encoding="utf-8")
    assert "get_commerce_integration_status" in source


def test_commerce_dry_run_flags_documented_in_integrations_module():
    source = (REPO_ROOT / "marketmind" / "commerce_integrations.py").read_text(
        encoding="utf-8"
    )
    for flag in COMMERCE_DRY_RUN_FLAGS:
        assert flag in source
    integrations_source = (
        REPO_ROOT / "marketmind" / "integrations_status.py"
    ).read_text(encoding="utf-8")
    assert COMMERCE_LIVE_WRITES_FLAG in integrations_source


@pytest.mark.parametrize("path", COMMERCE_API_READ_PATHS)
def test_commerce_read_api_paths_secret_free_with_credentials(
    commerce_contract_client, monkeypatch, path: str,
):
    monkeypatch.setenv("STRIPE_API_KEY", _STRIPE_KEY)
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", _SHOPIFY_TOKEN)
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", _GMAIL_SECRET)
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", _GMAIL_REFRESH)

    resp = commerce_contract_client.get(path)
    assert resp.status_code == 200
    _assert_no_secrets(resp.text)
    for marker in INTEGRATIONS_SECRET_LEAK_MARKERS:
        assert marker not in resp.text


def test_gmail_integrations_payload_uses_contract_keys_only(
    commerce_contract_client, monkeypatch,
):
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", _GMAIL_SECRET)
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", _GMAIL_REFRESH)

    gmail = commerce_contract_client.get("/operator/integrations").json()["gmail"]
    assert set(gmail) == set(GMAIL_INTEGRATION_KEYS)
    _assert_no_secrets(json.dumps(gmail))


def test_sources_stripe_safe_fails_without_credentials(commerce_contract_client):
    resp = commerce_contract_client.post("/sources/stripe/orders")
    assert resp.status_code == 409
    _assert_no_secrets(resp.text)


def test_api_shopify_execute_dry_run_secret_free(
    commerce_contract_client, commerce_contract_engine, monkeypatch,
):
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", _SHOPIFY_TOKEN)

    approval_store.create_approval(
        commerce_contract_engine,
        ApprovalRecord(
            approval_id="apr_shopify_contract",
            action="publish_shopify_product",
            risk_level=RiskLevel.HIGH,
            status=ApprovalStatus.PENDING,
            summary="Create Shopify draft",
            expected_cost=0.0,
            rollback_plan="Set back to draft.",
        ),
    )
    payload = ProductDraftPayload(
        title="Interior Kit",
        body_html="<p>Clean interior fast</p>",
        vendor="MarketMind",
        product_type="Auto Accessory",
        variants=(ShopifyVariant(price="59.00", sku="IK-1"),),
    )
    record_action_payload(
        commerce_contract_engine, "apr_shopify_contract", payload.to_dict()
    )
    approval_store.approve(commerce_contract_engine, "apr_shopify_contract")

    resp = commerce_contract_client.post(
        "/execute/apr_shopify_contract", json={"dry_run": True}
    )
    assert resp.status_code == 200
    assert resp.json()["detail"]["simulated"] is True
    _assert_no_secrets(resp.text)

    log_resp = commerce_contract_client.get("/execute/log")
    assert log_resp.status_code == 200
    _assert_no_secrets(log_resp.text)


def test_check_commerce_config_cli_stdout_secret_free(monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", _STRIPE_KEY)
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", _SHOPIFY_TOKEN)
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / CHECK_COMMERCE_CONFIG_CLI)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    _assert_no_secrets(proc.stdout)
    for marker in INTEGRATIONS_SECRET_LEAK_MARKERS:
        assert marker not in proc.stdout


def test_commerce_execute_paths_documented_in_contract():
    assert "/execute/{approval_id}" in COMMERCE_API_EXECUTE_PATHS
    assert "/execute/log" in COMMERCE_API_EXECUTE_PATHS
