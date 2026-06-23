"""Slice 55: integration readiness status."""

from marketmind.db.engine import make_engine
from marketmind.db.import_store import save_import
from marketmind.db.models import Base
from marketmind.importers import import_ad_report_csv
from marketmind.integrations_status import get_integrations_status

AD_CSV = """campaign_name,date,impressions,clicks,spend,purchases,revenue
Camp,2026-06-15,100,10,5.00,1,59.00
"""


def test_integrations_status_defaults(monkeypatch):
    monkeypatch.delenv("MARKETMIND_GMAIL_ENABLED", raising=False)
    monkeypatch.delenv("MARKETMIND_SNAPSHOT_PRUNE_ON_CYCLE", raising=False)
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    status = get_integrations_status(engine)
    assert status["gmail"]["mode"] == "draft_file_only"
    assert status["gmail"]["enabled"] is False
    assert status["stripe"]["configured"] is False
    assert status["shopify"]["configured"] is False
    assert status["ad_imports"]["has_latest_batch"] is False
    assert status["scheduler"]["prune_on_cycle"] is False


def test_integrations_status_reflects_ad_import_and_flags(monkeypatch):
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("MARKETMIND_SNAPSHOT_PRUNE_ON_CYCLE", "true")
    monkeypatch.setenv("MARKETMIND_SNAPSHOT_PRUNE_APPLY", "true")
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    save_import(engine, import_ad_report_csv(AD_CSV, source="ad_report_csv"))

    status = get_integrations_status(engine)
    assert status["gmail"]["enabled"] is True
    assert status["gmail"]["mode"] == "enabled_but_unconfigured"
    assert status["ad_imports"]["has_latest_batch"] is True
    assert status["scheduler"]["prune_apply"] is True
