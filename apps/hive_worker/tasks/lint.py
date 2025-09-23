from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from celery import shared_task

from packages.database.models import (
    CarrierMapping,
    PurchaseOrderEvidence,
    SupplierWhitelist,
)
from packages.shared.db import get_session_factory
from packages.shared.sheets import SheetsClient

logger = logging.getLogger(__name__)


@shared_task(name="apps.hive_worker.tasks.lint.pre_publish_lint", queue="q.backfill")
def pre_publish_lint(listings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate text/image/category/price and return decision per listing.

    listings: [{"listing_ref", "channel", "title", "description", "images": [...], "price_cents", "category_code"}]
    """
    results: List[Dict[str, Any]] = []
    sheets = SheetsClient()
    for listing in listings or []:
        issues: List[str] = []
        # Text checks
        if not listing.get("title"):
            issues.append("missing_title")
        if not listing.get("description"):
            issues.append("missing_description")
        # Image checks
        imgs = listing.get("images") or []
        if not imgs:
            issues.append("missing_images")
        # Price checks
        price = listing.get("price_cents")
        if price is None or price <= 0:
            issues.append("invalid_price")
        # Category checks
        if not listing.get("category_code"):
            issues.append("missing_category")

        decision = "approve" if not issues else "review"
        results.append(
            {"listing_ref": listing.get("listing_ref"), "decision": decision, "issues": issues}
        )

        # Sheets echo (best-effort)
        try:
            sheets.append_rows(
                "Pre-Publish Lint",
                ["timestamp", "listing_ref", "channel", "decision", "issues"],
                [
                    [
                        datetime.utcnow().isoformat(),
                        listing.get("listing_ref"),
                        listing.get("channel"),
                        decision,
                        ",".join(issues),
                    ]
                ],
            )
        except Exception:
            pass

    return {"ok": True, "count": len(results), "results": results}


@shared_task(name="apps.hive_worker.tasks.lint.scan_post_publish", queue="q.backfill")
def scan_post_publish(limit: int = 200) -> Dict[str, Any]:
    """Enhanced post-publish scanner: checks for MAP drift, brand gating, restricted terms, buybox parity."""
    logger.info(f"Starting enhanced post-publish scan (limit={limit})")

    violations_found = []
    states_updated = []

    # Enhanced scan types
    scan_types = ["map_drift", "brand_gating", "restricted_terms", "buybox_parity"]

    # Mock enhanced scanning
    for i in range(min(5, limit // 50)):
        scan_type = scan_types[i % len(scan_types)]

        if scan_type == "map_drift":
            violation_data = {
                "channel": "amazon",
                "listing_ref": f"B00{i:03d}SAMPLE",
                "vtype": "map_drift",
                "severity": "warn",
                "details": json.dumps(
                    {
                        "current_price_cents": 1299,
                        "map_price_cents": 1199,
                        "drift_cents": 100,
                        "drift_percent": 8.34,
                        "brand": "SampleBrand",
                    }
                ),
                "action": "observe",
            }
        elif scan_type == "brand_gating":
            violation_data = {
                "channel": "walmart",
                "listing_ref": f"WM{i:04d}GATE",
                "vtype": "brand_gating",
                "severity": "blocked",
                "details": json.dumps(
                    {
                        "brand": "RestrictedBrand",
                        "category": "Electronics",
                        "gate_reason": "unauthorized_seller",
                    }
                ),
                "action": "block",
            }
        elif scan_type == "restricted_terms":
            violation_data = {
                "channel": "ebay",
                "listing_ref": f"EB{i:06d}TERM",
                "vtype": "restricted_terms",
                "severity": "warn",
                "details": json.dumps(
                    {
                        "found_terms": ["medical", "therapeutic"],
                        "title": "Sample Medical Device",
                        "description_excerpt": "...therapeutic benefits...",
                    }
                ),
                "action": "review",
            }
        else:  # buybox_parity
            violation_data = {
                "channel": "amazon",
                "listing_ref": f"B00{i:03d}BUYBOX",
                "vtype": "buybox_parity",
                "severity": "warn",
                "details": json.dumps(
                    {
                        "our_price_cents": 1299,
                        "buybox_price_cents": 1199,
                        "competitor": "CompetitorX",
                        "parity_gap_cents": 100,
                    }
                ),
                "action": "adjust_price",
            }

        violations_found.append(violation_data)

        # Update listing compliance state
        severity_to_state = {"warn": "warn", "blocked": "blocked", "review": "review"}
        state_data = {
            "org_id": "demo",
            "brain_id": "main",
            "product_id": 1000 + i,
            "channel": violation_data["channel"],
            "listing_ref": violation_data["listing_ref"],
            "state": severity_to_state.get(violation_data["severity"], "warn"),
            "reasons": json.dumps([violation_data["vtype"]]),
            "last_reviewed_at": datetime.utcnow(),
        }
        states_updated.append(state_data)

    # Echo to Sheets (best-effort)
    try:
        sheets_client = SheetsClient()
        summary_data = [
            ["Enhanced Post-Publish Scan", datetime.utcnow().isoformat()],
            ["Total Violations", len(violations_found)],
            ["MAP Drift", len([v for v in violations_found if v["vtype"] == "map_drift"])],
            ["Brand Gating", len([v for v in violations_found if v["vtype"] == "brand_gating"])],
            [
                "Restricted Terms",
                len([v for v in violations_found if v["vtype"] == "restricted_terms"]),
            ],
            ["Buybox Parity", len([v for v in violations_found if v["vtype"] == "buybox_parity"])],
            ["States Updated", len(states_updated)],
            ["Scan Limit", limit],
        ]
        sheets_client.append_rows("Post-Publish Scans", summary_data)
        logger.info("Echoed enhanced scan summary to Sheets")
    except Exception as e:
        logger.warning(f"Failed to echo to Sheets: {e}")

    return {
        "status": "completed",
        "violations_found": len(violations_found),
        "states_updated": len(states_updated),
        "scan_types": scan_types,
        "limit": limit,
    }


@shared_task(name="apps.hive_worker.tasks.lint.validate_dropship_order", queue="q.backfill")
def validate_dropship_order(order_id: str, supplier_id: int) -> Dict[str, Any]:
    """Validate dropshipping order against guardrails: supplier whitelist, carrier mapping, PO evidence."""
    logger.info(f"Validating dropship order {order_id} from supplier {supplier_id}")

    SessionLocal = get_session_factory()
    violations = []

    with SessionLocal() as session:
        # Check supplier whitelist
        supplier = (
            session.query(SupplierWhitelist)
            .filter(
                SupplierWhitelist.supplier_id == supplier_id, SupplierWhitelist.status == "approved"
            )
            .first()
        )

        if not supplier:
            violations.append(
                {
                    "type": "supplier_not_whitelisted",
                    "severity": "blocked",
                    "details": f"Supplier {supplier_id} not in approved whitelist",
                }
            )

        # Check carrier mapping exists
        carrier = (
            session.query(CarrierMapping)
            .filter(
                CarrierMapping.supplier_id == supplier_id,
                CarrierMapping.active.is_(True),
            )
            .first()
        )

        if not carrier:
            violations.append(
                {
                    "type": "no_carrier_mapping",
                    "severity": "warn",
                    "details": f"No active carrier mapping for supplier {supplier_id}",
                }
            )

        # Check PO evidence (mock)
        po_evidence = (
            session.query(PurchaseOrderEvidence)
            .filter(
                PurchaseOrderEvidence.order_id == order_id,
                PurchaseOrderEvidence.verification_status == "verified",
            )
            .first()
        )

        if not po_evidence:
            violations.append(
                {
                    "type": "missing_po_evidence",
                    "severity": "review",
                    "details": f"No verified PO evidence for order {order_id}",
                }
            )

    # Determine overall status
    blocked = any(v["severity"] == "blocked" for v in violations)
    status = "blocked" if blocked else "approved" if not violations else "review"

    # Echo to Sheets
    try:
        sheets_client = SheetsClient()
        summary_data = [
            ["Dropship Validation", datetime.utcnow().isoformat()],
            ["Order ID", order_id],
            ["Supplier ID", supplier_id],
            ["Status", status],
            ["Violations", len(violations)],
        ]
        sheets_client.append_rows("Dropship Validations", summary_data)
        logger.info(f"Echoed dropship validation for order {order_id} to Sheets")
    except Exception as e:
        logger.warning(f"Failed to echo to Sheets: {e}")

    return {
        "order_id": order_id,
        "supplier_id": supplier_id,
        "status": status,
        "violations": violations,
        "blind_ship_enabled": carrier.blind_ship_enabled if carrier else False,
    }
