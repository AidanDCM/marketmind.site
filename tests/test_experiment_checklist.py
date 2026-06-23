"""Unit tests for marketmind.experiment_checklist."""

from marketmind.experiment_checklist import (
    build_experiment_scale_checklist,
    checklist_blockers,
    checklist_ready,
)


def _checklist(*, visits=300, orders=10, spend=200.0, cac=20.0, bep=25.0,
               status="active", losses=0, snap_date="2026-06-23"):
    return build_experiment_scale_checklist(
        experiment_id="exp_test",
        product_name="Widget Pro",
        status=status,
        qualified_visits=visits,
        orders=orders,
        total_ad_spend=spend,
        actual_cac=cac,
        break_even_cac=bep,
        consecutive_losing_periods=losses,
        latest_snapshot_date=snap_date,
    )


def test_ready_with_good_data():
    items = _checklist()
    assert checklist_ready(items) is True
    assert checklist_blockers(items) == []


def test_not_ready_when_inactive():
    items = _checklist(status="ended")
    assert checklist_ready(items) is False
    assert any("active" in b.lower() for b in checklist_blockers(items))


def test_not_ready_when_too_few_visits():
    items = _checklist(visits=50)
    assert checklist_ready(items) is False
    assert any("visit" in b.lower() for b in checklist_blockers(items))


def test_not_ready_when_too_few_orders():
    items = _checklist(orders=2)
    assert checklist_ready(items) is False
    assert any("order" in b.lower() for b in checklist_blockers(items))


def test_not_ready_when_cac_above_break_even():
    items = _checklist(cac=30.0, bep=25.0)
    assert checklist_ready(items) is False
    assert any("break-even" in b.lower() for b in checklist_blockers(items))


def test_not_ready_when_consecutive_losses():
    items = _checklist(losses=2)
    assert checklist_ready(items) is False
    assert any("losing" in b.lower() for b in checklist_blockers(items))


def test_not_ready_when_no_snapshot():
    items = _checklist(snap_date=None)
    assert checklist_ready(items) is False
    assert any("snapshot" in b.lower() for b in checklist_blockers(items))


def test_not_ready_when_spend_too_low():
    items = _checklist(spend=10.0)
    assert checklist_ready(items) is False
    assert any("spend" in b.lower() for b in checklist_blockers(items))


def test_items_have_expected_fields():
    items = _checklist()
    for item in items:
        assert hasattr(item, "item_id")
        assert hasattr(item, "description")
        assert hasattr(item, "required")
        assert hasattr(item, "passed")
        assert hasattr(item, "evidence")
