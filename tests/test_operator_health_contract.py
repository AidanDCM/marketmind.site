"""Phase B pass 16 (rotation 3): operator health contract parity and deeper coverage."""

from __future__ import annotations

import re
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from marketmind.api.app import app
from marketmind.db.approval_store import create_approval
from marketmind.db.engine import make_engine
from marketmind.db.models import Base, ExperimentRow
from marketmind.docs_contract import REPO_ROOT
from marketmind.operator_health import build_operator_health
from marketmind.operator_health_contract import (
    ATTENTION_RULINGS,
    DESKTOP_API_CLIENT_PATH,
    DESKTOP_READINESS_CONSTANTS_PATH,
    EXPERIMENT_RULING_BLOCKER_PATTERN,
    GMAIL_LIVE_NOT_READY_WARNING,
    GMAIL_SECRET_MISSING_WARNING,
    MISSING_SNAPSHOT_WARNING_PATTERN,
    OPERATOR_HEALTH_API_PATHS,
    OPERATOR_HEALTH_DESKTOP_API_PATHS,
    OPERATOR_HEALTH_EXTENDED_API_PATHS,
    OPERATOR_HEALTH_PANEL_DATE_QUERY,
    OPERATOR_LOG_MISSING_WARNING,
    OPERATOR_READINESS_CLI,
    OPERATOR_READINESS_CLI_API_FLAG,
    OPERATOR_READINESS_DATE_QUERY,
    OPERATOR_READINESS_STRICT_QUERY,
    PENDING_APPROVALS_BLOCKER_PATTERN,
    READINESS_BANNER_ACTION_LABELS,
    SHOPIFY_LIVE_WARNING_PREFIX,
    SNAPSHOT_GAP_TRUNCATION_LIMIT,
    STRIPE_LIVE_WARNING_PREFIX,
    format_experiment_ruling_blocker,
    format_missing_snapshot_warning,
    format_pending_approvals_blocker,
)
from marketmind.operator_preflight import run_preflight
from marketmind.schemas import ApprovalRecord, ApprovalStatus, RiskLevel


@pytest.fixture
def health_engine():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def health_client(health_engine):
    app.state.engine = health_engine
    with TestClient(app) as client:
        yield client
    app.state.engine = None


def _pending_approval(engine) -> None:
    create_approval(
        engine,
        ApprovalRecord(
            approval_id="apr_contract_pending",
            action="scale_campaign",
            risk_level=RiskLevel.HIGH,
            status=ApprovalStatus.PENDING,
            summary="Pending scale",
            expected_cost=100.0,
            rollback_plan="Pause",
        ),
    )


def _add_active_experiment(engine, experiment_id: str) -> None:
    with Session(engine) as session:
        session.add(
            ExperimentRow(
                experiment_id=experiment_id,
                product_name=f"Product {experiment_id}",
                break_even_cac=25.0,
                status="active",
            )
        )
        session.commit()


def test_blocker_formatters_match_desktop_regex_patterns():
    pending = format_pending_approvals_blocker(3)
    assert PENDING_APPROVALS_BLOCKER_PATTERN.fullmatch(pending)
    ruling = format_experiment_ruling_blocker("exp-42", "kill")
    assert EXPERIMENT_RULING_BLOCKER_PATTERN.fullmatch(ruling)
    snapshot = format_missing_snapshot_warning(
        2, "2026-06-23", ["exp-a", "exp-b"]
    )
    assert MISSING_SNAPSHOT_WARNING_PATTERN.fullmatch(snapshot)


def test_truncated_snapshot_warning_matches_desktop_parser():
    ids = [f"exp_{i}" for i in range(6)]
    warning = format_missing_snapshot_warning(6, "2026-06-23", ids)
    assert MISSING_SNAPSHOT_WARNING_PATTERN.fullmatch(warning)
    match = MISSING_SNAPSHOT_WARNING_PATTERN.fullmatch(warning)
    assert match is not None
    assert match.group(3).endswith("…")


def test_warning_prefix_constants_match_desktop_readiness_banner_actions():
    ts = (REPO_ROOT / DESKTOP_READINESS_CONSTANTS_PATH).read_text(encoding="utf-8")

    def _extract(name: str) -> str:
        match = re.search(rf'export const {name}\s*=\s*"([^"]+)"', ts)
        assert match, f"missing desktop constant {name}"
        return match.group(1)

    assert _extract("GMAIL_LIVE_WARNING") == GMAIL_LIVE_NOT_READY_WARNING
    assert _extract("GMAIL_SECRET_WARNING") == GMAIL_SECRET_MISSING_WARNING
    assert _extract("STRIPE_LIVE_WARNING_PREFIX") == STRIPE_LIVE_WARNING_PREFIX
    assert _extract("SHOPIFY_LIVE_WARNING_PREFIX") == SHOPIFY_LIVE_WARNING_PREFIX


def test_preflight_pending_blocker_uses_contract_formatter(health_engine):
    _pending_approval(health_engine)
    preflight = run_preflight(health_engine)
    assert preflight.blockers == [format_pending_approvals_blocker(1)]


def test_preflight_experiment_ruling_blocker_uses_contract_formatter(health_client):
    health_client.post(
        "/snapshots",
        json={
            "experiment_id": "exp_kill_contract",
            "product_name": "Widget",
            "break_even_cac": 25.0,
            "snapshot_date": "2026-06-23",
            "qualified_visits": 800,
            "orders": 0,
            "total_ad_spend": 100.0,
            "total_revenue": 0.0,
            "refund_count": 0,
            "actual_shipping_cost": 5.0,
            "planned_shipping_cost": 5.0,
            "add_to_cart_count": 0,
            "consecutive_losing_periods": 0,
            "budget_cap": 500.0,
        },
    )
    preflight = health_client.get("/operator/preflight").json()
    assert preflight["experiments_needing_attention"]
    ruling = preflight["experiments_needing_attention"][0]["ruling"]
    assert ruling in ATTENTION_RULINGS
    expected = format_experiment_ruling_blocker("exp_kill_contract", ruling)
    assert expected in preflight["blockers"]


@pytest.mark.parametrize("path", OPERATOR_HEALTH_API_PATHS)
def test_operator_health_api_paths_return_200_on_empty_db(health_client, path: str):
    resp = health_client.get(path)
    assert resp.status_code == 200


def test_health_panel_date_query_scopes_snapshot_gaps(health_client, health_engine):
    _add_active_experiment(health_engine, "exp_gap_contract")
    resp = health_client.get("/operator/health-panel?date=2026-06-15")
    data = resp.json()
    assert data["snapshot_gaps"]["snapshot_date"] == "2026-06-15"
    assert data["snapshot_gaps"]["missing_count"] == 1
    expected = format_missing_snapshot_warning(1, "2026-06-15", ["exp_gap_contract"])
    assert expected in data["warnings"]


def test_build_operator_health_snapshot_warning_uses_contract_formatter(
    monkeypatch, tmp_path, health_engine,
):
    monkeypatch.chdir(tmp_path)
    _add_active_experiment(health_engine, "exp_gap_contract")
    health = build_operator_health(health_engine, snapshot_date="2026-06-23")
    expected = format_missing_snapshot_warning(1, "2026-06-23", ["exp_gap_contract"])
    assert expected in health["warnings"]


def test_live_writes_emits_stripe_and_shopify_contract_warnings(
    monkeypatch, tmp_path, health_engine,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MARKETMIND_ENABLE_LIVE_WRITES", "true")
    health = build_operator_health(health_engine)
    warnings = health["warnings"]
    assert any(STRIPE_LIVE_WARNING_PREFIX in w for w in warnings)
    assert any(SHOPIFY_LIVE_WARNING_PREFIX in w for w in warnings)


def test_strict_readiness_fails_when_operator_log_warning_present(
    health_client, monkeypatch, tmp_path,
):
    monkeypatch.chdir(tmp_path)
    loose = health_client.get("/operator/readiness").json()
    strict = health_client.get("/operator/readiness?strict=true").json()
    assert OPERATOR_LOG_MISSING_WARNING in loose["warnings"]
    assert loose["ready"] is True
    assert strict["ready"] is False


def test_operator_readiness_cli_exists_and_documents_strict_flag():
    cli = REPO_ROOT / OPERATOR_READINESS_CLI
    assert cli.is_file()
    proc = subprocess.run(
        [sys.executable, str(cli), "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "--strict" in proc.stdout


def test_snapshot_gap_truncation_limit_matches_contract():
    assert SNAPSHOT_GAP_TRUNCATION_LIMIT == 5


def test_desktop_client_documents_operator_health_api_paths():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    for path in (
        *OPERATOR_HEALTH_API_PATHS,
        *OPERATOR_HEALTH_DESKTOP_API_PATHS,
    ):
        assert path in text


def test_readiness_banner_action_labels_match_desktop_module():
    text = (REPO_ROOT / DESKTOP_READINESS_CONSTANTS_PATH).read_text(encoding="utf-8")
    for label in READINESS_BANNER_ACTION_LABELS.values():
        assert label in text


def test_contract_blocker_formatters_match_banner_regex_patterns():
    pending = format_pending_approvals_blocker(2)
    assert PENDING_APPROVALS_BLOCKER_PATTERN.fullmatch(pending)
    ruling = format_experiment_ruling_blocker("exp_banner", "pause_ads")
    assert EXPERIMENT_RULING_BLOCKER_PATTERN.fullmatch(ruling)
    assert ruling.endswith("pause_ads' — action required")
    snapshot = format_missing_snapshot_warning(3, "2026-06-23", ["a", "b", "c"])
    assert MISSING_SNAPSHOT_WARNING_PATTERN.fullmatch(snapshot)


@pytest.mark.parametrize("path", OPERATOR_HEALTH_EXTENDED_API_PATHS)
def test_operator_health_extended_api_paths_return_200(health_client, path: str):
    resp = health_client.get(path)
    assert resp.status_code == 200, path


def test_health_panel_includes_integrations_snapshot(health_client):
    data = health_client.get("/operator/health-panel").json()
    assert "integrations" in data
    assert "gmail" in data["integrations"]
    assert "stripe" in data["integrations"]
    assert "shopify" in data["integrations"]


def test_readiness_date_query_scopes_snapshot_gaps(health_client, health_engine):
    _add_active_experiment(health_engine, "exp_readiness_date")
    data = health_client.get(
        f"/operator/readiness?{OPERATOR_READINESS_DATE_QUERY}=2026-06-10"
    ).json()
    gaps = data["snapshot_gaps"]
    assert gaps["snapshot_date"] == "2026-06-10"
    assert gaps["missing_count"] == 1
    expected = format_missing_snapshot_warning(1, "2026-06-10", ["exp_readiness_date"])
    assert expected in data["warnings"]


def test_gmail_secret_missing_warning_when_live_writes_without_secret(
    monkeypatch, tmp_path, health_engine,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MARKETMIND_ENABLE_LIVE_WRITES", "true")
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "rtok")
    monkeypatch.delenv("GMAIL_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("MARKETMIND_GMAIL_DRY_RUN", "false")
    health = build_operator_health(health_engine)
    assert GMAIL_SECRET_MISSING_WARNING in health["warnings"]


def test_operator_router_documents_strict_and_date_query_params():
    source = (REPO_ROOT / "marketmind/api/routers/operator.py").read_text(
        encoding="utf-8"
    )
    assert OPERATOR_READINESS_STRICT_QUERY in source
    assert OPERATOR_READINESS_DATE_QUERY in source
    assert OPERATOR_HEALTH_PANEL_DATE_QUERY in source


def test_operator_readiness_cli_documents_api_flag():
    source = (REPO_ROOT / OPERATOR_READINESS_CLI).read_text(encoding="utf-8")
    assert OPERATOR_READINESS_CLI_API_FLAG in source
    assert "fetch_operator_readiness_from_api" in source


def test_health_panel_empty_date_query_returns_422(health_client):
    resp = health_client.get(f"/operator/health-panel?{OPERATOR_HEALTH_PANEL_DATE_QUERY}=")
    assert resp.status_code == 422
