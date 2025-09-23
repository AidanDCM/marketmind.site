"""Ledger service for maintaining financial records in Google Sheets."""

from typing import Optional, TypedDict

from packages.integrations.google.sheets_client import sheets_client
from packages.ledger.config import LedgerSettings


class OrderRecord(TypedDict):
    """Structure for order records in the ledger."""

    ts: str
    channel: str
    order_id: str
    sku: str
    qty: int
    item_total: float
    shipping_total: float
    tax_total: float
    tax_model: str  # 'marketplace_collected' or 'seller_collected'
    fees_total: float
    net_revenue: float
    cogs: float
    est_shipping_cost: float
    return_reserve: float
    net_profit: float
    customer_region: str
    fulfillment_status: str


class TaxDetailRecord(TypedDict):
    """Structure for tax detail records."""

    order_id: str
    ship_state: str
    ship_county: Optional[str]
    taxable_amount: float
    tax_collected: float
    nexus_flag: bool


class MarketplaceTaxRecord(TypedDict):
    """Structure for marketplace-collected tax records."""

    date: str
    channel: str
    jurisdiction: str
    tax_collected_by_marketplace: float


class PricingDecisionRecord(TypedDict):
    """Structure for pricing decision records."""

    ts: str
    asin: str
    sku: str
    landed_cost: float
    comp_best_price: Optional[float]
    proposed_price: float
    min_margin: float
    map_price: Optional[float]
    respect_map: bool
    reason: str
    sim_live: str  # 'sim' or 'live'
    effect: Optional[float]  # Actual margin/volume effect if known


class SupplierPORecord(TypedDict):
    """Structure for supplier purchase order records."""

    po_ts: str
    supplier: str
    supplier_sku: str
    order_id: str
    cost: float
    lead_time: int  # days
    status: str
    tracking_no: Optional[str]
    carrier: Optional[str]
    delivery_ts: Optional[str]


class AccountHealthRecord(TypedDict):
    """Structure for account health metrics."""

    date: str
    channel: str
    buybox_pct: Optional[float]  # Percentage of listings winning buybox
    late_ship_rate: Optional[float]  # Percentage of orders shipped late
    valid_tracking_pct: Optional[float]  # Percentage with valid tracking
    odr: Optional[float]  # Order defect rate
    tickets_opened: Optional[int]  # Customer service tickets
    tickets_sla_met: Optional[int]  # Tickets resolved within SLA


class LedgerService:
    """Service for maintaining financial records in Google Sheets."""

    def __init__(self, config: Optional[LedgerSettings] = None):
        """Initialize the ledger service."""
        self.config = config
        self.sheets = sheets_client

    async def record_order(self, order: OrderRecord) -> bool:
        """Record an order in the ledger."""
        row = [
            order["ts"],
            order["channel"],
            order["order_id"],
            order["sku"],
            order["qty"],
            order["item_total"],
            order["shipping_total"],
            order["tax_total"],
            order["tax_model"],
            order["fees_total"],
            order["net_revenue"],
            order["cogs"],
            order["est_shipping_cost"],
            order["return_reserve"],
            order["net_profit"],
            order["customer_region"],
            order["fulfillment_status"],
        ]

        result = await self.sheets.batch_append_rows(
            spreadsheet_id=self.config.LEDGER_SPREADSHEET_ID if self.config else None,
            sheet_name=self.config.SHEET_ORDERS if self.config else "Orders Ledger",
            rows=[row],
            dedupe_key_columns=[2, 3],  # Dedupe on order_id + sku
        )

        return result.success

    async def record_tax_detail(self, tax_detail: TaxDetailRecord) -> bool:
        """Record tax detail for an order."""
        row = [
            tax_detail["order_id"],
            tax_detail["ship_state"],
            tax_detail.get("ship_county", ""),
            tax_detail["taxable_amount"],
            tax_detail["tax_collected"],
            "Yes" if tax_detail["nexus_flag"] else "No",
        ]

        result = await self.sheets.batch_append_rows(
            spreadsheet_id=self.config.LEDGER_SPREADSHEET_ID if self.config else None,
            sheet_name=self.config.SHEET_TAX_DETAIL if self.config else "Sales-Tax Detail",
            rows=[row],
            dedupe_key_columns=[0],  # Dedupe on order_id
        )

        return result.success

    async def record_marketplace_tax(self, tax_record: MarketplaceTaxRecord) -> bool:
        """Record marketplace-collected tax."""
        row = [
            tax_record["date"],
            tax_record["channel"],
            tax_record["jurisdiction"],
            tax_record["tax_collected_by_marketplace"],
        ]

        result = await self.sheets.batch_append_rows(
            spreadsheet_id=self.config.LEDGER_SPREADSHEET_ID if self.config else None,
            sheet_name=(
                self.config.SHEET_MARKETPLACE_TAX if self.config else "Marketplace-Collected Tax"
            ),
            rows=[row],
            dedupe_key_columns=[0, 1, 2],  # Dedupe on date + channel + jurisdiction
        )

        return result.success

    async def record_pricing_decision(self, decision: PricingDecisionRecord) -> bool:
        """Record a pricing decision."""
        row = [
            decision["ts"],
            decision["asin"],
            decision["sku"],
            decision["landed_cost"],
            decision.get("comp_best_price", ""),
            decision["proposed_price"],
            decision["min_margin"],
            decision.get("map_price", ""),
            "Yes" if decision["respect_map"] else "No",
            decision["reason"],
            decision["sim_live"],
            decision.get("effect", ""),
        ]

        result = await self.sheets.batch_append_rows(
            spreadsheet_id=self.config.LEDGER_SPREADSHEET_ID if self.config else None,
            sheet_name=self.config.SHEET_PRICING_DECISIONS if self.config else "Pricing Decisions",
            rows=[row],
            # No deduplication for pricing decisions (log all changes)
        )

        return result.success

    async def record_supplier_po(self, po: SupplierPORecord) -> bool:
        """Record a supplier purchase order."""
        row = [
            po["po_ts"],
            po["supplier"],
            po["supplier_sku"],
            po["order_id"],
            po["cost"],
            po["lead_time"],
            po["status"],
            po.get("tracking_no", ""),
            po.get("carrier", ""),
            po.get("delivery_ts", ""),
        ]

        result = await self.sheets.batch_append_rows(
            spreadsheet_id=self.config.LEDGER_SPREADSHEET_ID if self.config else None,
            sheet_name=self.config.SHEET_SUPPLIER_POS if self.config else "Supplier POs",
            rows=[row],
            dedupe_key_columns=[3, 2],  # Dedupe on order_id + supplier_sku
        )

        return result.success

    async def record_account_health(self, record: AccountHealthRecord) -> bool:
        """Record account health metrics in the ledger.

        Args:
            record: The account health record to record

        Returns:
            bool: True if the record was successfully recorded, False otherwise
        """
        # Convert the record to a list of values in the correct order
        row = [
            record["date"],
            record["channel"],
            record.get("buybox_pct", ""),
            record.get("late_ship_rate", ""),
            record.get("valid_tracking_pct", ""),
            record.get("odr", ""),
            record.get("tickets_opened", ""),
            record.get("tickets_sla_met", ""),
        ]

        result = await self.sheets.batch_append_rows(
            spreadsheet_id=self.config.LEDGER_SPREADSHEET_ID if self.config else None,
            sheet_name=self.config.SHEET_ACCOUNT_HEALTH if self.config else "Account Health",
            rows=[row],
            dedupe_key_columns=[0, 1],  # Dedupe on date + channel
        )

        return result.success


# Global instance for easy import
ledger_service = LedgerService()
