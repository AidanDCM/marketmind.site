
from marketmind import (
    ImportRowStatus,
    import_ad_report_csv,
    import_orders_csv,
    import_products_csv,
)

# ---------------------------------------------------------------------------
# Product CSV importer
# ---------------------------------------------------------------------------

PRODUCT_HEADER = "product_name,sale_price,product_cost,shipping_cost,niche"

PRODUCT_VALID = f"""{PRODUCT_HEADER}
Daily Driver Interior Refresh Kit,59.0,18.0,4.0,Car Accessories
"""

PRODUCT_MISSING_NAME = f"""{PRODUCT_HEADER}
,59.0,18.0,4.0,Car Accessories
"""

PRODUCT_BAD_PRICE = f"""{PRODUCT_HEADER}
Some Kit,NOT_A_NUMBER,18.0,4.0,Car Accessories
"""

PRODUCT_ALIAS_HEADER = "title,price,cost,shipping,category\nKit A,49.0,12.0,3.5,Home"


def test_product_valid_row_is_ok():
    result = import_products_csv(PRODUCT_VALID)
    assert result.total_rows == 1
    assert len(result.ok_rows) == 1
    assert result.ok_rows[0].status == ImportRowStatus.OK
    assert result.ok_rows[0].data["product_name"] == "Daily Driver Interior Refresh Kit"


def test_product_missing_name_goes_to_review():
    result = import_products_csv(PRODUCT_MISSING_NAME)
    assert len(result.review_rows) == 1
    assert "product_name" in result.review_rows[0].notes


def test_product_bad_price_goes_to_review():
    result = import_products_csv(PRODUCT_BAD_PRICE)
    assert len(result.review_rows) == 1
    assert "sale_price" in result.review_rows[0].notes


def test_product_column_aliases_resolve():
    result = import_products_csv(PRODUCT_ALIAS_HEADER)
    assert len(result.ok_rows) == 1
    assert result.ok_rows[0].data["product_name"] == "Kit A"
    assert result.ok_rows[0].data["sale_price"] == "49.0"


def test_product_empty_csv_produces_zero_rows():
    result = import_products_csv(PRODUCT_HEADER + "\n")
    assert result.total_rows == 0
    assert len(result.ok_rows) == 0


# ---------------------------------------------------------------------------
# Ad report CSV importer
# ---------------------------------------------------------------------------

AD_HEADER = "campaign_name,date,impressions,clicks,spend,purchases,revenue"

AD_VALID = f"""{AD_HEADER}
Interior Kit — US,2026-06-15,1000,50,25.00,3,177.00
"""

AD_MISSING_CAMPAIGN = f"""{AD_HEADER}
,2026-06-15,1000,50,25.00,3,177.00
"""

AD_BAD_SPEND = f"""{AD_HEADER}
Interior Kit,2026-06-15,1000,50,NOT_A_NUMBER,3,177.00
"""

AD_ALIAS_HEADER = (
    "campaign,day,impr,link clicks,cost,conversions,purchase_value\n"
    "Kit B,2026-06-15,500,20,10.00,1,59.00"
)


def test_ad_valid_row_is_ok():
    result = import_ad_report_csv(AD_VALID)
    assert len(result.ok_rows) == 1
    assert result.ok_rows[0].data["campaign_name"] == "Interior Kit — US"


def test_ad_missing_campaign_goes_to_review():
    result = import_ad_report_csv(AD_MISSING_CAMPAIGN)
    assert len(result.review_rows) == 1
    assert "campaign_name" in result.review_rows[0].notes


def test_ad_bad_spend_goes_to_review():
    result = import_ad_report_csv(AD_BAD_SPEND)
    assert len(result.review_rows) == 1
    assert "spend" in result.review_rows[0].notes


def test_ad_column_aliases_resolve():
    result = import_ad_report_csv(AD_ALIAS_HEADER)
    assert len(result.ok_rows) == 1
    assert result.ok_rows[0].data["campaign_name"] == "Kit B"


# ---------------------------------------------------------------------------
# Orders CSV importer
# ---------------------------------------------------------------------------

ORDER_HEADER = "order_id,date,product_name,sale_price,status,refunded,shipping_cost"

ORDER_VALID = f"""{ORDER_HEADER}
ORD-001,2026-06-15,Daily Driver Interior Refresh Kit,59.00,fulfilled,no,4.00
"""

ORDER_MISSING_ID = f"""{ORDER_HEADER}
,2026-06-15,Kit,59.00,fulfilled,no,4.00
"""

ORDER_BAD_PRICE = f"""{ORDER_HEADER}
ORD-002,2026-06-15,Kit,OOPS,fulfilled,no,4.00
"""

ORDER_ALIAS_HEADER = (
    "order number,created at,item name,total,fulfillment status,refund,ship cost\n"
    "ORD-003,2026-06-15,Kit C,49.00,unfulfilled,no,3.50"
)


def test_order_valid_row_is_ok():
    result = import_orders_csv(ORDER_VALID)
    assert len(result.ok_rows) == 1
    assert result.ok_rows[0].data["order_id"] == "ORD-001"


def test_order_missing_id_goes_to_review():
    result = import_orders_csv(ORDER_MISSING_ID)
    assert len(result.review_rows) == 1
    assert "order_id" in result.review_rows[0].notes


def test_order_bad_price_goes_to_review():
    result = import_orders_csv(ORDER_BAD_PRICE)
    assert len(result.review_rows) == 1
    assert "sale_price" in result.review_rows[0].notes


def test_order_column_aliases_resolve():
    result = import_orders_csv(ORDER_ALIAS_HEADER)
    assert len(result.ok_rows) == 1
    assert result.ok_rows[0].data["order_id"] == "ORD-003"


def test_import_result_total_rows_matches():
    csv_text = ORDER_HEADER + "\n"
    for i in range(5):
        csv_text += f"ORD-{i:03d},2026-06-15,Kit,59.00,fulfilled,no,4.00\n"
    result = import_orders_csv(csv_text)
    assert result.total_rows == 5
    assert len(result.ok_rows) == 5
