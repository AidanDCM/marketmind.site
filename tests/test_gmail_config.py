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
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "sec")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "rtok")
    monkeypatch.setenv("MARKETMIND_GMAIL_DRY_RUN", "false")
    cfg = get_gmail_config()
    assert cfg.mode == "live_send"
    assert cfg.live_ready is True


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


def test_create_gmail_draft_live_requires_client_secret(monkeypatch):
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "rtok")
    monkeypatch.setenv("MARKETMIND_GMAIL_DRY_RUN", "false")
    monkeypatch.setenv("MARKETMIND_ENABLE_LIVE_WRITES", "true")
    monkeypatch.delenv("GMAIL_CLIENT_SECRET", raising=False)
    with pytest.raises(ValueError, match="GMAIL_CLIENT_SECRET"):
        create_supplier_gmail_draft(
            approval=_approval(),
            to_address="buyer@acme.example",
            subject="S",
            body="B",
        )


def test_create_gmail_draft_live_calls_api(monkeypatch):
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "sec")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "rtok")
    monkeypatch.setenv("MARKETMIND_GMAIL_DRY_RUN", "false")
    monkeypatch.setenv("MARKETMIND_ENABLE_LIVE_WRITES", "true")

    def fake_create_draft(self, *, to_address, subject, body):
        assert subject == "Sample inquiry"
        return {"id": "draft_live_99"}

    monkeypatch.setattr(
        "marketmind.adapters.gmail_client.GmailClient.create_draft",
        fake_create_draft,
    )

    result = create_supplier_gmail_draft(
        approval=_approval(),
        to_address="buyer@acme.example",
        subject="Sample inquiry",
        body="Hello",
    )
    assert result["simulated"] is False
    assert result["gmail_draft_id"] == "draft_live_99"


def test_encode_raw_message_roundtrip():
    from marketmind.adapters.gmail_client import _encode_raw_message

    raw = _encode_raw_message(
        to_address="buyer@example.com",
        subject="Test",
        body="Body text",
        from_email="me@example.com",
    )
    assert isinstance(raw, str)
    assert "=" not in raw


def test_live_writes_allowed_default_false(monkeypatch):
    monkeypatch.delenv("MARKETMIND_ENABLE_LIVE_WRITES", raising=False)
    assert live_writes_allowed() is False
