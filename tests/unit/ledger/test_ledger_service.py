"""Unit tests for the LedgerService class."""

from unittest.mock import AsyncMock, MagicMock

import pytest

# Skip if Google client libs are not available since Ledger depends on them indirectly
try:  # pragma: no cover - import guard
    import google  # noqa: F401
except Exception:  # pragma: no cover
    pytest.skip(
        "Skipping LedgerService tests: google client libraries not installed",
        allow_module_level=True,
    )

from packages.ledger.config import LedgerSettings
from packages.ledger.service import (
    AccountHealthRecord,
    LedgerService,
    MarketplaceTaxRecord,
    OrderRecord,
    PricingDecisionRecord,
    SupplierPORecord,
    TaxDetailRecord,
)


@pytest.fixture
def test_settings():
    """Test settings for the ledger service."""
    return LedgerSettings(
        LEDGER_SPREADSHEET_ID="test_spreadsheet_id",
        GOOGLE_CREDENTIALS_PATH="test_credentials.json",
        BATCH_SIZE=10,
        MAX_RETRIES=2,
        RETRY_DELAY=1,
    )


@pytest.fixture
def ledger_service(test_settings):
    """Create a LedgerService instance with a mock Google Sheets client."""
    service = LedgerService(config=test_settings)
    service.sheets = AsyncMock()
    service.sheets.batch_append_rows.return_value = MagicMock(success=True, rows_processed=1)
    return service


@pytest.mark.asyncio
async def test_record_order(ledger_service):
    """Test recording an order in the ledger."""
    # Test data
    order = OrderRecord(
        ts="2023-01-01T12:00:00Z",
        channel="amazon",
        order_id="123-1234567-1234567",
        sku="PROD-001",
        qty=1,
        item_total=29.99,
        shipping_total=0.00,
        tax_total=2.40,
        tax_model="marketplace_collected",
        fees_total=4.50,
        net_revenue=25.49,
        cogs=12.50,
        est_shipping_cost=3.50,
        return_reserve=1.25,
        net_profit=8.24,
        customer_region="US-WA",
        fulfillment_status="shipped",
    )

    # Call the method
    result = await ledger_service.record_order(order)

    # Assertions
    assert result is True

    # Verify the correct data was passed to batch_append_rows
    ledger_service.sheets.batch_append_rows.assert_called_once()

    # Get the arguments passed to batch_append_rows
    args, kwargs = ledger_service.sheets.batch_append_rows.call_args

    assert kwargs["sheet_name"] == "Orders Ledger"
    assert kwargs["spreadsheet_id"] == "test_spreadsheet_id"
    assert kwargs["dedupe_key_columns"] == [2, 3]  # order_id + sku

    # Verify the row data
    rows = kwargs["rows"]
    assert len(rows) == 1

    row = rows[0]
    assert row[0] == "2023-01-01T12:00:00Z"  # ts
    assert row[1] == "amazon"  # channel
    assert row[2] == "123-1234567-1234567"  # order_id
    assert row[3] == "PROD-001"  # sku
    assert row[4] == 1  # qty
    assert row[5] == 29.99  # item_total
    assert row[6] == 0.0  # shipping_total
    assert row[7] == 2.4  # tax_total
    assert row[8] == "marketplace_collected"  # tax_model
    assert row[9] == 4.5  # fees_total
    assert row[10] == 25.49  # net_revenue
    assert row[11] == 12.5  # cogs
    assert row[12] == 3.5  # est_shipping_cost
    assert row[13] == 1.25  # return_reserve
    assert row[14] == 8.24  # net_profit
    assert row[15] == "US-WA"  # customer_region
    assert row[16] == "shipped"  # fulfillment_status


@pytest.mark.asyncio
async def test_record_tax_detail(ledger_service):
    """Test recording tax details in the ledger."""
    # Test data
    tax_detail = TaxDetailRecord(
        order_id="123-1234567-1234567",
        ship_state="WA",
        ship_county="King",
        taxable_amount=29.99,
        tax_collected=2.40,
        nexus_flag=True,
    )

    # Call the method
    result = await ledger_service.record_tax_detail(tax_detail)

    # Assertions
    assert result is True

    # Verify the correct data was passed to batch_append_rows
    ledger_service.sheets.batch_append_rows.assert_called_once()

    # Get the arguments passed to batch_append_rows
    args, kwargs = ledger_service.sheets.batch_append_rows.call_args

    assert kwargs["sheet_name"] == "Sales-Tax Detail"
    assert kwargs["spreadsheet_id"] == "test_spreadsheet_id"
    assert kwargs["dedupe_key_columns"] == [0]  # order_id

    # Verify the row data
    rows = kwargs["rows"]
    assert len(rows) == 1

    row = rows[0]
    assert row[0] == "123-1234567-1234567"  # order_id
    assert row[1] == "WA"  # ship_state
    assert row[2] == "King"  # ship_county
    assert row[3] == 29.99  # taxable_amount
    assert row[4] == 2.40  # tax_collected
    assert row[5] == "Yes"  # nexus_flag (converted to Yes/No)


@pytest.mark.asyncio
async def test_record_marketplace_tax(ledger_service):
    """Test recording marketplace-collected tax in the ledger."""
    # Test data
    tax_record = MarketplaceTaxRecord(
        date="2023-01-01",
        channel="amazon",
        jurisdiction="US-WA",
        tax_collected_by_marketplace=120.50,
    )

    # Call the method
    result = await ledger_service.record_marketplace_tax(tax_record)

    # Assertions
    assert result is True

    # Verify the correct data was passed to batch_append_rows
    ledger_service.sheets.batch_append_rows.assert_called_once()

    # Get the arguments passed to batch_append_rows
    args, kwargs = ledger_service.sheets.batch_append_rows.call_args

    assert kwargs["sheet_name"] == "Marketplace-Collected Tax"
    assert kwargs["spreadsheet_id"] == "test_spreadsheet_id"
    assert kwargs["dedupe_key_columns"] == [0, 1, 2]  # date + channel + jurisdiction

    # Verify the row data
    rows = kwargs["rows"]
    assert len(rows) == 1

    row = rows[0]
    assert row[0] == "2023-01-01"  # date
    assert row[1] == "amazon"  # channel
    assert row[2] == "US-WA"  # jurisdiction
    assert row[3] == 120.50  # tax_collected_by_marketplace


@pytest.mark.asyncio
async def test_record_pricing_decision(ledger_service):
    """Test recording a pricing decision in the ledger."""
    # Test data
    decision = PricingDecisionRecord(
        ts="2023-01-01T12:00:00Z",
        asin="B0ABCDE123",
        sku="PROD-001",
        landed_cost=15.00,
        comp_best_price=29.99,
        proposed_price=27.99,
        min_margin=0.30,
        map_price=29.99,
        respect_map=True,
        reason="Competitive adjustment",
        sim_live="live",
        effect=0.35,  # 35% margin
    )

    # Call the method
    result = await ledger_service.record_pricing_decision(decision)

    # Assertions
    assert result is True

    # Verify the correct data was passed to batch_append_rows
    ledger_service.sheets.batch_append_rows.assert_called_once()

    # Get the arguments passed to batch_append_rows
    args, kwargs = ledger_service.sheets.batch_append_rows.call_args

    assert kwargs["sheet_name"] == "Pricing Decisions"
    assert kwargs["spreadsheet_id"] == "test_spreadsheet_id"
    assert "dedupe_key_columns" not in kwargs  # No deduplication for pricing decisions

    # Verify the row data
    rows = kwargs["rows"]
    assert len(rows) == 1

    row = rows[0]
    assert row[0] == "2023-01-01T12:00:00Z"  # ts
    assert row[1] == "B0ABCDE123"  # asin
    assert row[2] == "PROD-001"  # sku
    assert row[3] == 15.00  # landed_cost
    assert row[4] == 29.99  # comp_best_price
    assert row[5] == 27.99  # proposed_price
    assert row[6] == 0.30  # min_margin
    assert row[7] == 29.99  # map_price
    assert row[8] == "Yes"  # respect_map (converted to Yes/No)
    assert row[9] == "Competitive adjustment"  # reason
    assert row[10] == "live"  # sim_live
    assert row[11] == 0.35  # effect


@pytest.mark.asyncio
async def test_record_supplier_po(ledger_service):
    """Test recording a supplier purchase order in the ledger."""
    # Test data
    po = SupplierPORecord(
        po_ts="2023-01-01T12:00:00Z",
        supplier="CJ Dropshipping",
        supplier_sku="CJ-12345",
        order_id="123-1234567-1234567",
        cost=12.50,
        lead_time=5,
        status="ordered",
        tracking_no="1Z9999999999999999",
        carrier="UPS",
        delivery_ts="2023-01-06T14:30:00Z",
    )

    # Call the method
    result = await ledger_service.record_supplier_po(po)

    # Assertions
    assert result is True

    # Verify the correct data was passed to batch_append_rows
    ledger_service.sheets.batch_append_rows.assert_called_once()

    # Get the arguments passed to batch_append_rows
    args, kwargs = ledger_service.sheets.batch_append_rows.call_args

    assert kwargs["sheet_name"] == "Supplier POs"
    assert kwargs["spreadsheet_id"] == "test_spreadsheet_id"
    assert kwargs["dedupe_key_columns"] == [3, 2]  # order_id + supplier_sku

    # Verify the row data
    rows = kwargs["rows"]
    assert len(rows) == 1

    row = rows[0]
    assert row[0] == "2023-01-01T12:00:00Z"  # po_ts
    assert row[1] == "CJ Dropshipping"  # supplier
    assert row[2] == "CJ-12345"  # supplier_sku
    assert row[3] == "123-1234567-1234567"  # order_id
    assert row[4] == 12.50  # cost
    assert row[5] == 5  # lead_time
    assert row[6] == "ordered"  # status
    assert row[7] == "1Z9999999999999999"  # tracking_no
    assert row[8] == "UPS"  # carrier
    assert row[9] == "2023-01-06T14:30:00Z"  # delivery_ts


@pytest.mark.asyncio
async def test_record_account_health(ledger_service):
    """Test recording account health metrics in the ledger."""
    # Test data
    health = AccountHealthRecord(
        date="2023-01-01",
        channel="amazon",
        buybox_pct=95.5,
        late_ship_rate=2.1,
        valid_tracking_pct=98.7,
        odr=0.5,
        tickets_opened=3,
        tickets_sla_met=2,
    )

    # Call the method
    result = await ledger_service.record_account_health(health)

    # Assertions
    assert result is True

    # Verify the correct data was passed to batch_append_rows
    ledger_service.sheets.batch_append_rows.assert_called_once()

    # Get the arguments passed to batch_append_rows
    args, kwargs = ledger_service.sheets.batch_append_rows.call_args

    assert kwargs["sheet_name"] == "Account Health"
    assert kwargs["spreadsheet_id"] == "test_spreadsheet_id"
    assert kwargs["dedupe_key_columns"] == [0, 1]  # date + channel

    # Verify the row data
    rows = kwargs["rows"]
    assert len(rows) == 1

    row = rows[0]
    assert row[0] == "2023-01-01"  # date
    assert row[1] == "amazon"  # channel
    assert row[2] == 95.5  # buybox_pct
    assert row[3] == 2.1  # late_ship_rate
    assert row[4] == 98.7  # valid_tracking_pct
    assert row[5] == 0.5  # odr
    assert row[6] == 3  # tickets_opened
    assert row[7] == 2  # tickets_sla_met
