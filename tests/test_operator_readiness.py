"""Slice 63: unified operator readiness check."""

from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.operator_readiness import (
    evaluate_operator_readiness,
    fetch_operator_readiness_from_api,
    masked_gmail_summary,
)


def test_masked_gmail_summary_never_includes_secrets(monkeypatch):
    monkeypatch.setenv("GMAIL_CLIENT_ID", "my-client-id")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "my-client-secret")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "my-refresh-token")
    summary = masked_gmail_summary()
    dumped = str(summary)
    assert "my-client" not in dumped
    assert "my-refresh" not in dumped
    assert summary["has_client_id"] is True
    assert summary["has_client_secret"] is True


def test_evaluate_operator_readiness_empty_db(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    result = evaluate_operator_readiness(engine)
    assert result.ready is True
    assert result.blockers == ()
    assert "gmail" in result.report
    assert "commerce" in result.report
    assert result.report["preflight"]["safe_to_operate"] is True


def test_evaluate_operator_readiness_strict_fails_on_warnings(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    loose = evaluate_operator_readiness(engine, strict=False)
    strict = evaluate_operator_readiness(engine, strict=True)
    assert loose.ready is True
    assert strict.ready is False
    assert any("Operator event log" in w for w in strict.warnings)


def test_evaluate_operator_readiness_snapshot_date(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    result = evaluate_operator_readiness(engine, snapshot_date="2026-06-18")
    assert result.report["snapshot_gaps"]["snapshot_date"] == "2026-06-18"


def test_fetch_operator_readiness_from_api():
    payload = {
        "ready": True,
        "blockers": [],
        "warnings": ["Operator event log not found"],
        "safe_to_operate": True,
        "gmail": {"mode": "draft_file_only", "live_ready": False, "dry_run": True},
        "commerce": {
            "stripe": {"configured": False, "live_ready": False},
            "shopify": {"configured": False, "live_ready": False},
        },
        "preflight": {"safe_to_operate": True},
        "snapshot_gaps": {
            "snapshot_date": "2026-06-23",
            "active_count": 0,
            "missing_count": 0,
            "missing": [],
            "all_recorded": False,
        },
    }

    def fetch(url: str, token: str | None) -> dict:
        del token
        assert url.endswith("/operator/readiness?date=2026-06-20&strict=true")
        return payload

    result = fetch_operator_readiness_from_api(
        "http://127.0.0.1:8000",
        snapshot_date="2026-06-20",
        strict=True,
        fetch=fetch,
    )
    assert result.ready is True
    assert result.warnings == ("Operator event log not found",)
