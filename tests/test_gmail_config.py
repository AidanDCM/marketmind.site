"""Slice 56: Gmail config and client tests."""

import pytest

from marketmind.adapters.gmail_client import create_supplier_gmail_draft
from marketmind.gmail_config import get_gmail_config, live_writes_allowed
from marketmind.schemas import ApprovalRecord, ApprovalStatus, RiskLevel


def _approval() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_gmail_1",
        action="contact_supplier",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.APPROVED,
        summary="Contact Acme",
        expected_cost=0.0,
        rollback_plan="Discard draft",
    )


def test_gmail_config_defaults(monkeypatch):
    monkeypatch.delenv("MARKETMIND_GMAIL_ENABLED", raising=False)
    cfg = get_gmail_config()
    assert cfg.enabled is False
    assert cfg.mode == "draft_file_only"
    assert cfg.dry_run is True


def test_gmail_config_simulate_when_wired(monkeypatch):
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "rtok")
    cfg = get_gmail_config()
    assert cfg.wired is True
    assert cfg.mode == "simulate"


def test_gmail_config_live_mode_requires_dry_run_off(monkeypatch):
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "rtok")
    monkeypatch.setenv("MARKETMIND_GMAIL_DRY_RUN", "false")
    cfg = get_gmail_config()
    assert cfg.mode == "live_send"


def test_create_gmail_draft_simulated(monkeypatch):
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "rtok")
    result = create_supplier_gmail_draft(
        approval=_approval(),
        to_address="buyer@acme.example",
        subject="Sample inquiry",
        body="Hello",
        supplier_name="Acme",
    )
    assert result["simulated"] is True
    assert result["gmail_draft_id"].startswith("sim_gmail_")


def test_create_gmail_draft_rejects_when_disabled(monkeypatch):
    monkeypatch.delenv("MARKETMIND_GMAIL_ENABLED", raising=False)
    with pytest.raises(ValueError, match="disabled"):
        create_supplier_gmail_draft(
            approval=_approval(),
            to_address="",
            subject="S",
            body="B",
        )


def test_live_writes_allowed_default_false(monkeypatch):
    monkeypatch.delenv("MARKETMIND_ENABLE_LIVE_WRITES", raising=False)
    assert live_writes_allowed() is False
