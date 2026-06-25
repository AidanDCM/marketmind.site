"""Slice 58: consolidated operator health panel."""

from sqlalchemy.orm import Session

from marketmind.db.engine import make_engine
from marketmind.db.models import Base, ExperimentRow
from marketmind.operator_health import build_operator_health


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


def test_build_operator_health_snapshot_gap_warning(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    _add_active_experiment(engine, "exp_gap")
    health = build_operator_health(engine, snapshot_date="2026-06-23")
    assert health["snapshot_gaps"]["missing_count"] == 1
    assert any(
        w == "1 active experiment(s) missing snapshot for 2026-06-23: exp_gap"
        for w in health["warnings"]
    )


def test_build_operator_health_truncates_snapshot_gap_ids(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    for i in range(6):
        _add_active_experiment(engine, f"exp_{i}")
    health = build_operator_health(engine, snapshot_date="2026-06-23")
    gap_warnings = [w for w in health["warnings"] if "missing snapshot" in w]
    assert len(gap_warnings) == 1
    assert "exp_0, exp_1, exp_2, exp_3, exp_4…" in gap_warnings[0]


def test_build_operator_health_warns_gmail_missing_secret(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "rtok")
    monkeypatch.setenv("MARKETMIND_GMAIL_DRY_RUN", "false")
    monkeypatch.delenv("GMAIL_CLIENT_SECRET", raising=False)
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    health = build_operator_health(engine)
    assert any(
        w == "Gmail live mode enabled but GMAIL_CLIENT_SECRET is missing"
        for w in health["warnings"]
    )


def test_build_operator_health_warns_shopify_live_writes(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MARKETMIND_ENABLE_LIVE_WRITES", "true")
    monkeypatch.setenv("STRIPE_API_KEY", "sk_test")
    monkeypatch.setenv("MARKETMIND_STRIPE_DRY_RUN", "false")
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    health = build_operator_health(engine)
    assert any("Shopify is not live-ready" in w for w in health["warnings"])
