from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from .config import get_settings

try:
    import gspread  # type: ignore
except Exception:  # pragma: no cover
    gspread = None  # lazy fallback


class SheetsClient:
    def __init__(self, spreadsheet_id: Optional[str] = None) -> None:
        settings = get_settings()
        self.spreadsheet_id = spreadsheet_id or settings.sheets.ledger_spreadsheet_id
        # Settings schema uses service_account_json_path
        self.creds_path = settings.sheets.service_account_json_path
        self._gc = None
        self._is_configured = bool(self.spreadsheet_id and self.creds_path and gspread)
        self._row_hashes: Dict[str, set] = {}  # Track written row hashes per tab

    @property
    def configured(self) -> bool:
        return self._is_configured

    def _ensure_client(self):
        if not self._is_configured:
            return None
        if self._gc is not None:
            return self._gc
        try:
            if os.path.isfile(self.creds_path):
                self._gc = gspread.service_account(filename=self.creds_path)
            else:
                # Try as JSON string
                data = json.loads(self.creds_path)
                self._gc = gspread.service_account_from_dict(data)
            return self._gc
        except Exception:
            # Misconfiguration; mark as not configured
            self._is_configured = False
            return None

    def _open_sheet(self):
        gc = self._ensure_client()
        if not gc:
            return None
        try:
            return gc.open_by_key(self.spreadsheet_id)
        except Exception:
            return None

    def ensure_tab_headers(self, tab: str, headers: Sequence[str]) -> bool:
        sh = self._open_sheet()
        if not sh:
            return False
        try:
            try:
                ws = sh.worksheet(tab)
            except Exception:
                ws = sh.add_worksheet(title=tab, rows=100, cols=max(10, len(headers)))
            curr = ws.row_values(1)
            if curr != list(headers):
                ws.resize(rows=1)
                ws.update("A1", [list(headers)])
            return True
        except Exception:
            return False

    def append_rows(self, tab: str, headers: Sequence[str], rows: List[Sequence[object]]) -> bool:
        """Append rows with basic deduplication (no hash check)"""
        sh = self._open_sheet()
        if not sh:
            return False
        try:
            ws = None
            try:
                ws = sh.worksheet(tab)
            except Exception:
                ws = sh.add_worksheet(
                    title=tab, rows=max(100, len(rows) + 1), cols=max(10, len(headers))
                )
            self.ensure_tab_headers(tab, headers)
            if rows:
                ws.append_rows(rows)
            return True
        except Exception:
            return False

    def _row_hash(self, row: Sequence[object]) -> str:
        """Generate hash for row idempotency"""
        row_str = "|".join(str(cell) for cell in row)
        return hashlib.sha1(row_str.encode()).hexdigest()[:12]

    def append_rows_idempotent(
        self,
        tab: str,
        headers: Sequence[str],
        rows: List[Sequence[object]],
        hash_columns: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Append rows with hash-based idempotency

        Args:
            tab: Sheet tab name
            headers: Column headers
            rows: Rows to append
            hash_columns: Column indices to use for hash (default: all columns)

        Returns:
            Dict with 'success', 'appended_count', 'skipped_count'
        """
        if not rows:
            return {"success": True, "appended_count": 0, "skipped_count": 0}

        sh = self._open_sheet()
        if not sh:
            return {
                "success": False,
                "appended_count": 0,
                "skipped_count": 0,
                "error": "sheet_unavailable",
            }

        try:
            # Ensure worksheet exists
            try:
                ws = sh.worksheet(tab)
            except Exception:
                ws = sh.add_worksheet(
                    title=tab, rows=max(100, len(rows) + 10), cols=max(10, len(headers))
                )

            # Ensure headers
            self.ensure_tab_headers(tab, headers)

            # Load existing row hashes if not cached
            if tab not in self._row_hashes:
                self._load_existing_hashes(ws, tab, hash_columns)

            # Filter out duplicate rows
            new_rows = []
            skipped = 0

            for row in rows:
                # Use specified columns or all for hash
                hash_row = (
                    [row[i] for i in (hash_columns or range(len(row)))] if hash_columns else row
                )
                row_hash = self._row_hash(hash_row)

                if row_hash not in self._row_hashes[tab]:
                    new_rows.append(row)
                    self._row_hashes[tab].add(row_hash)
                else:
                    skipped += 1

            # Append new rows in batches
            appended = 0
            if new_rows:
                batch_size = 100  # Google Sheets API limit
                for i in range(0, len(new_rows), batch_size):
                    batch = new_rows[i : i + batch_size]
                    ws.append_rows(batch)
                    appended += len(batch)
                    time.sleep(0.1)  # Rate limit courtesy

            return {"success": True, "appended_count": appended, "skipped_count": skipped}

        except Exception as e:
            return {"success": False, "appended_count": 0, "skipped_count": 0, "error": str(e)}

    def _load_existing_hashes(self, ws, tab: str, hash_columns: Optional[List[int]] = None):
        """Load existing row hashes from sheet for deduplication"""
        try:
            # Get all values (skip header row)
            all_values = ws.get_all_values()[1:]  # Skip header
            self._row_hashes[tab] = set()

            for row in all_values:
                if not any(row):  # Skip empty rows
                    continue
                hash_row = (
                    [row[i] for i in (hash_columns or range(len(row)))] if hash_columns else row
                )
                row_hash = self._row_hash(hash_row)
                self._row_hashes[tab].add(row_hash)

        except Exception:
            # If we can't load existing hashes, start fresh
            self._row_hashes[tab] = set()

    def health_check(self) -> Dict[str, Any]:
        """Health check for Sheets integration"""
        if not self._is_configured:
            return {"ok": False, "error": "not_configured"}

        try:
            start_time = time.time()
            gc = self._ensure_client()
            if not gc:
                return {"ok": False, "error": "auth_failed"}

            # Try to open the spreadsheet
            sh = self._open_sheet()
            if not sh:
                return {"ok": False, "error": "spreadsheet_not_found"}

            latency_ms = int((time.time() - start_time) * 1000)
            return {"ok": True, "latency_ms": latency_ms, "spreadsheet_id": self.spreadsheet_id}

        except Exception as e:
            return {"ok": False, "error": str(e)}


# Ledger-specific writers with predefined schemas
class LedgerWriter:
    """High-level writer for standard ledger tabs"""

    def __init__(self, spreadsheet_id: Optional[str] = None):
        self.client = SheetsClient(spreadsheet_id)

    def write_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Write order to Orders Ledger tab"""
        headers = [
            "timestamp",
            "channel",
            "order_id",
            "sku",
            "qty",
            "item_total",
            "shipping_total",
            "tax_total",
            "tax_model",
            "fees_total",
            "net_revenue",
            "cogs",
            "est_shipping_cost",
            "return_reserve",
            "net_profit",
            "customer_region",
            "fulfillment_status",
        ]

        row = [
            order_data.get("timestamp", datetime.utcnow().isoformat()),
            order_data.get("channel", ""),
            order_data.get("order_id", ""),
            order_data.get("sku", ""),
            order_data.get("qty", 0),
            order_data.get("item_total", 0.0),
            order_data.get("shipping_total", 0.0),
            order_data.get("tax_total", 0.0),
            order_data.get("tax_model", "marketplace_collected"),
            order_data.get("fees_total", 0.0),
            order_data.get("net_revenue", 0.0),
            order_data.get("cogs", 0.0),
            order_data.get("est_shipping_cost", 0.0),
            order_data.get("return_reserve", 0.0),
            order_data.get("net_profit", 0.0),
            order_data.get("customer_region", ""),
            order_data.get("fulfillment_status", "pending"),
        ]

        # Use order_id + timestamp for hash uniqueness
        hash_columns = [1, 2]  # channel, order_id
        return self.client.append_rows_idempotent("Orders Ledger", headers, [row], hash_columns)

    def write_pricing_decision(self, pricing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Write pricing decision to Pricing Decisions tab"""
        headers = [
            "timestamp",
            "asin_sku",
            "landed_cost",
            "comp_best_price",
            "proposed_price",
            "min_margin",
            "map_price",
            "respect_map",
            "reason",
            "sim_live",
            "effect",
        ]

        row = [
            pricing_data.get("timestamp", datetime.utcnow().isoformat()),
            pricing_data.get("asin_sku", ""),
            pricing_data.get("landed_cost", 0.0),
            pricing_data.get("comp_best_price", 0.0),
            pricing_data.get("proposed_price", 0.0),
            pricing_data.get("min_margin", 0.0),
            pricing_data.get("map_price", 0.0),
            pricing_data.get("respect_map", True),
            pricing_data.get("reason", ""),
            pricing_data.get("sim_live", "simulation"),
            pricing_data.get("effect", ""),
        ]

        # Use asin_sku + timestamp bucket for hash
        hash_columns = [1]  # asin_sku
        return self.client.append_rows_idempotent("Pricing Decisions", headers, [row], hash_columns)

    def write_supplier_po(self, po_data: Dict[str, Any]) -> Dict[str, Any]:
        """Write supplier PO to Supplier PO & Tracking tab"""
        headers = [
            "po_timestamp",
            "supplier",
            "supplier_sku",
            "order_id",
            "cost",
            "lead_time",
            "status",
            "tracking_no",
            "carrier",
            "delivery_timestamp",
        ]

        row = [
            po_data.get("po_timestamp", datetime.utcnow().isoformat()),
            po_data.get("supplier", ""),
            po_data.get("supplier_sku", ""),
            po_data.get("order_id", ""),
            po_data.get("cost", 0.0),
            po_data.get("lead_time", 0),
            po_data.get("status", "placed"),
            po_data.get("tracking_no", ""),
            po_data.get("carrier", ""),
            po_data.get("delivery_timestamp", ""),
        ]

        hash_columns = [3]  # order_id
        return self.client.append_rows_idempotent(
            "Supplier PO & Tracking", headers, [row], hash_columns
        )


# Global instance for easy access
_ledger_writer = None


def get_ledger_writer() -> LedgerWriter:
    global _ledger_writer
    if _ledger_writer is None:
        _ledger_writer = LedgerWriter()
    return _ledger_writer
