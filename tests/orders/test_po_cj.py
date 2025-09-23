from packages.orders.po_cj import CJPOClient


def test_cj_po_idempotency():
    client = CJPOClient(api_key=None)
    payload = {"order_id": 123, "items": [("SKU", 1)]}
    res1 = client.create_po(payload)
    res2 = client.create_po(payload)
    assert res1.idempotency_key == res2.idempotency_key
    assert res1.supplier_po_ref == res2.supplier_po_ref


def test_cj_tracking_shape():
    client = CJPOClient(api_key=None)
    tracking = client.get_tracking("PO-ABCDEFGH")
    assert set(tracking.keys()) == {"carrier", "service", "tracking_no"}
