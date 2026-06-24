"""Slice 58: consolidated operator health panel."""

from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.operator_health import build_operator_health


def test_build_operator_health_empty_db():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    health = build_operator_health(engine)
    assert "preflight" in health
    assert "integrations" in health
    assert health["portfolio"]["total_experiments"] == 0
    assert health["ad_spend"]["has_data"] is False
    assert health["checklist"]["min_visits"] == 100


def test_build_operator_health_warns_missing_operator_log(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    health = build_operator_health(engine)
    assert any("Operator event log" in w for w in health["warnings"])


def test_build_operator_health_warns_live_writes_without_stripe(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MARKETMIND_ENABLE_LIVE_WRITES", "true")
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    health = build_operator_health(engine)
    assert any("Stripe is not live-ready" in w for w in health["warnings"])


def test_build_operator_health_snapshot_date_param():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    health = build_operator_health(engine, snapshot_date="2026-06-15")
    assert health["snapshot_gaps"]["snapshot_date"] == "2026-06-15"
