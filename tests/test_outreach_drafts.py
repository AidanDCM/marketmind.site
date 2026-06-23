"""Tests for marketmind.outreach_drafts and supplier pipeline."""

import pytest

from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.outreach_drafts import build_supplier_outreach_draft
from marketmind.pipeline import prepare_supplier_outreach_for_approval


def test_build_draft():
    draft = build_supplier_outreach_draft(
        supplier_name="Acme Supplies",
        product_name="Interior Kit",
        sample_quantity=2,
        target_unit_cost=12.5,
    )
    assert "Acme Supplies" in draft.body
    assert draft.dry_run is True
    assert "Interior Kit" in draft.subject


def test_build_draft_requires_names():
    with pytest.raises(ValueError):
        build_supplier_outreach_draft(supplier_name="", product_name="X")


def test_prepare_supplier_outreach_creates_pending_approval():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    record = prepare_supplier_outreach_for_approval(
        engine,
        supplier_name="Acme",
        product_name="Kit",
        expected_cost=25.0,
    )
    assert record.action == "contact_supplier"
    assert record.status.value == "pending"
