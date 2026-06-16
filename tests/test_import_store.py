"""Slice 29: import batch persistence."""

import pytest

from marketmind.db.engine import make_engine
from marketmind.db.import_store import get_import, list_imports, save_import
from marketmind.db.models import Base
from marketmind.schemas import ImportResult, ImportRow, ImportRowStatus


@pytest.fixture
def engine():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


def _result(source: str, n: int = 2) -> ImportResult:
    rows = [
        ImportRow(
            row_number=i + 1,
            status=ImportRowStatus.OK,
            data={"order_id": f"ord_{i}", "sale_price": "9.99"},
        )
        for i in range(n)
    ]
    return ImportResult(source=source, total_rows=n, ok_rows=rows, review_rows=[])


def test_save_and_get(engine):
    result = _result("stripe_charges", 3)
    batch_id = save_import(engine, result)
    assert isinstance(batch_id, int)
    batch = get_import(engine, batch_id)
    assert batch is not None
    assert batch["source"] == "stripe_charges"
    assert batch["total_rows"] == 3
    assert batch["ok_count"] == 3
    assert batch["review_count"] == 0
    assert len(batch["rows"]) == 3
    assert batch["rows"][0]["order_id"] == "ord_0"


def test_get_missing_returns_none(engine):
    assert get_import(engine, 9999) is None


def test_list_empty(engine):
    assert list_imports(engine) == []


def test_list_returns_newest_first(engine):
    save_import(engine, _result("shopify_orders", 1))
    save_import(engine, _result("stripe_charges", 2))
    batches = list_imports(engine)
    assert len(batches) == 2
    assert batches[0]["source"] == "stripe_charges"
    assert batches[1]["source"] == "shopify_orders"


def test_list_filter_by_source(engine):
    save_import(engine, _result("shopify_orders"))
    save_import(engine, _result("stripe_charges"))
    save_import(engine, _result("shopify_orders"))
    batches = list_imports(engine, source="shopify_orders")
    assert len(batches) == 2
    assert all(b["source"] == "shopify_orders" for b in batches)


def test_list_limit(engine):
    for _ in range(5):
        save_import(engine, _result("stripe_charges", 1))
    assert len(list_imports(engine, limit=3)) == 3


def test_list_does_not_include_rows_json(engine):
    save_import(engine, _result("stripe_charges"))
    batch = list_imports(engine)[0]
    assert "rows" not in batch
    assert "rows_json" not in batch


def test_get_includes_rows(engine):
    save_import(engine, _result("shopify_products", 4))
    batch = get_import(engine, 1)
    assert "rows" in batch
    assert len(batch["rows"]) == 4
