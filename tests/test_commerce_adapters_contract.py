"""Phase B pass 33 (rotation 5): commerce adapters contract parity and deeper coverage."""

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
    COMMERCE_AD_IMPORT_API_PATHS,
    COMMERCE_AD_SUMMARY_HAS_DATA_KEY,
    COMMERCE_API_EXECUTE_PATHS,
    COMMERCE_API_READ_PATHS,
    COMMERCE_DRY_RUN_FLAGS,
    COMMERCE_HANDLER_ACTIONS,
    COMMERCE_IMPORT_API_PATHS,
    COMMERCE_IMPORT_BATCH_NOT_FOUND_DETAIL,
    COMMERCE_IMPORT_EMPTY_CSV_DETAIL,
    COMMERCE_IMPORT_HISTORY_API_PATHS,
    COMMERCE_IMPORTS_ROUTER_PATH,
    COMMERCE_INTEGRATIONS_MODULE_PATH,
    COMMERCE_LIVE_WRITES_FLAG,
    COMMERCE_READINESS_COMMERCE_KEY,
    COMMERCE_SOURCE_API_PATHS,
    COMMERCE_SOURCES_ROUTER_PATH,
    DESKTOP_API_CLIENT_PATH,
    DESKTOP_LIVE_DATA_COMPONENT_PATH,
    GMAIL_INTEGRATION_KEYS,
    IMPORT_HISTORY_SOURCE_QUERY,
    INTEGRATIONS_LIVE_WRITES_KEY,
    INTEGRATIONS_SECRET_LEAK_MARKERS,
    LIVE_DATA_CREDENTIALS_409_HINT,
    LIVE_DATA_IMPORT_CSV_BUTTON,
    LIVE_DATA_PAGE_TITLE,
    LIVE_DATA_PULL_BUTTON,
    LIVE_DATA_SHOPIFY_ORDERS_LABEL,
    LIVE_DATA_SHOPIFY_PRODUCTS_LABEL,
    LIVE_DATA_STRIPE_SOURCE_LABEL,
    SECRET_MASK_VECTORS,
    SHOPIFY_INTEGRATION_KEYS,
    STRIPE_INTEGRATION_KEYS,
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


def test_stripe_integrations_payload_uses_contract_keys_only(
    commerce_contract_client, monkeypatch,
):
    monkeypatch.setenv("STRIPE_API_KEY", _STRIPE_KEY)
    stripe = commerce_contract_client.get("/operator/integrations").json()["stripe"]
    assert set(stripe) == set(STRIPE_INTEGRATION_KEYS)
    _assert_no_secrets(json.dumps(stripe))


def test_shopify_integrations_payload_uses_contract_keys_only(
    commerce_contract_client, monkeypatch,
):
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", _SHOPIFY_TOKEN)
    shopify = commerce_contract_client.get("/operator/integrations").json()["shopify"]
    assert set(shopify) == set(SHOPIFY_INTEGRATION_KEYS)
    _assert_no_secrets(json.dumps(shopify))


def test_integrations_payload_includes_live_writes_key(commerce_contract_client):
    data = commerce_contract_client.get("/operator/integrations").json()
    assert INTEGRATIONS_LIVE_WRITES_KEY in data
    assert "enabled" in data[INTEGRATIONS_LIVE_WRITES_KEY]


def test_desktop_client_documents_import_history_and_ad_paths():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    for path in (
        *COMMERCE_IMPORT_HISTORY_API_PATHS,
        *COMMERCE_AD_IMPORT_API_PATHS,
    ):
        normalized = path.replace("{batch_id}", "")
        assert normalized in text or path in text


def test_sources_router_documents_contract_source_paths():
    source = (REPO_ROOT / COMMERCE_SOURCES_ROUTER_PATH).read_text(encoding="utf-8")
    for path in COMMERCE_SOURCE_API_PATHS:
        suffix = path.removeprefix("/sources")
        assert suffix in source


def test_imports_router_documents_contract_import_paths():
    source = (REPO_ROOT / COMMERCE_IMPORTS_ROUTER_PATH).read_text(encoding="utf-8")
    for path in (
        *COMMERCE_IMPORT_API_PATHS,
        *COMMERCE_AD_IMPORT_API_PATHS,
    ):
        suffix = path.removeprefix("/imports")
        assert suffix in source
    assert COMMERCE_IMPORT_BATCH_NOT_FOUND_DETAIL in source
    assert COMMERCE_IMPORT_EMPTY_CSV_DETAIL in source


def test_import_batch_unknown_returns_404_with_contract_detail(commerce_contract_client):
    resp = commerce_contract_client.get("/imports/99999")
    assert resp.status_code == 404
    assert COMMERCE_IMPORT_BATCH_NOT_FOUND_DETAIL in resp.json()["detail"]


def test_desktop_client_documents_get_import_batch_and_source_query():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    assert "getImportBatch" in text
    assert f"?{IMPORT_HISTORY_SOURCE_QUERY}=" in text
    assert "pullAndSaveShopifyOrders" in text
    assert "pullAndSaveShopifyProducts" in text


def test_readiness_commerce_payload_uses_integration_keys(
    commerce_contract_client, monkeypatch,
):
    monkeypatch.setenv("STRIPE_API_KEY", _STRIPE_KEY)
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", _SHOPIFY_TOKEN)
    commerce = commerce_contract_client.get("/operator/readiness").json()[
        COMMERCE_READINESS_COMMERCE_KEY
    ]
    assert set(commerce["stripe"]) == set(STRIPE_INTEGRATION_KEYS)
    assert set(commerce["shopify"]) == set(SHOPIFY_INTEGRATION_KEYS)
    _assert_no_secrets(json.dumps(commerce))


def test_import_pull_shopify_products_safe_fails_without_credentials(
    commerce_contract_client,
):
    resp = commerce_contract_client.post("/imports/pull/shopify/products")
    assert resp.status_code == 409
    _assert_no_secrets(resp.text)


def test_commerce_integrations_module_documents_canonical_env_names():
    source = (REPO_ROOT / COMMERCE_INTEGRATIONS_MODULE_PATH).read_text(encoding="utf-8")
    assert "CANONICAL_STRIPE_ENV_NAMES" in source
    assert "CANONICAL_SHOPIFY_DOMAIN" in source
    assert "CANONICAL_SHOPIFY_TOKEN_NAMES" in source


def test_live_data_component_documents_shopify_products_label():
    text = (REPO_ROOT / DESKTOP_LIVE_DATA_COMPONENT_PATH).read_text(encoding="utf-8")
    assert LIVE_DATA_SHOPIFY_PRODUCTS_LABEL in text
    assert "importAdCsv" in text


def test_import_history_accepts_source_query_param(commerce_contract_client):
    resp = commerce_contract_client.get("/imports?source=stripe_charges")
    assert resp.status_code == 200
    assert resp.json() == []


def test_import_history_list_returns_200_on_empty_db(commerce_contract_client):
    resp = commerce_contract_client.get("/imports")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.parametrize(
    "path",
    [
        "/sources/shopify/orders",
        "/sources/shopify/products",
    ],
)
def test_shopify_source_paths_safe_fail_without_credentials(
    commerce_contract_client, path: str,
):
    resp = commerce_contract_client.post(path)
    assert resp.status_code == 409
    _assert_no_secrets(resp.text)


def test_import_pull_stripe_safe_fails_without_credentials(commerce_contract_client):
    resp = commerce_contract_client.post("/imports/pull/stripe/orders")
    assert resp.status_code == 409
    _assert_no_secrets(resp.text)


def test_ad_csv_empty_body_returns_422(commerce_contract_client):
    resp = commerce_contract_client.post("/imports/ads/csv", json={"csv_text": "  "})
    assert resp.status_code == 422
    assert COMMERCE_IMPORT_EMPTY_CSV_DETAIL in resp.json()["detail"]


def test_ad_spend_summary_empty_db_returns_has_data_false(commerce_contract_client):
    data = commerce_contract_client.get("/imports/ads/summary").json()
    assert data[COMMERCE_AD_SUMMARY_HAS_DATA_KEY] is False
    assert data["summary"] is None


def test_live_data_component_documents_source_labels_and_pull_ui():
    text = (REPO_ROOT / DESKTOP_LIVE_DATA_COMPONENT_PATH).read_text(encoding="utf-8")
    assert LIVE_DATA_PAGE_TITLE in text
    assert LIVE_DATA_PULL_BUTTON in text
    assert LIVE_DATA_IMPORT_CSV_BUTTON in text
    assert LIVE_DATA_STRIPE_SOURCE_LABEL in text
    assert LIVE_DATA_SHOPIFY_ORDERS_LABEL in text
    assert LIVE_DATA_SHOPIFY_PRODUCTS_LABEL in text
    assert LIVE_DATA_CREDENTIALS_409_HINT in text


@pytest.mark.parametrize(
    ("name", "vector"),
    sorted(SECRET_MASK_VECTORS.items()),
)
def test_secret_mask_vectors_fully_redacted(name: str, vector: str):
    masked = mask_secret(vector)
    for marker in INTEGRATIONS_SECRET_LEAK_MARKERS:
        if marker in vector:
            assert marker not in masked or "***REDACTED***" in masked
    assert vector != masked or "***REDACTED***" in masked, name
