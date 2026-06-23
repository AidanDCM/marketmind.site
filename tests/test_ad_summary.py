"""Slice 54: Ad spend summary from persisted import batches."""

from marketmind.ad_summary import summarize_latest_ad_batch
from marketmind.db.engine import make_engine
from marketmind.db.import_store import save_import
from marketmind.db.models import Base
from marketmind.importers import import_ad_report_csv

AD_CSV = """campaign_name,date,impressions,clicks,spend,purchases,revenue
Interior Kit — US,2026-06-15,1000,50,25.00,3,177.00
Kit B,2026-06-16,500,20,10.00,1,59.00
"""


def test_summarize_latest_ad_batch_aggregates_totals():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    result = import_ad_report_csv(AD_CSV, source="ad_report_csv")
    save_import(engine, result)

    summary = summarize_latest_ad_batch(engine)
    assert summary is not None
    assert summary.campaigns == 2
    assert summary.total_spend == 35.0
    assert summary.total_clicks == 70
    assert summary.total_impressions == 1500
    assert summary.total_purchases == 4
    assert summary.total_revenue == 236.0


def test_summarize_latest_ad_batch_empty_when_no_imports():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    assert summarize_latest_ad_batch(engine) is None
