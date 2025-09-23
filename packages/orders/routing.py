"""Routing engine scaffold.

Selects supplier and shipping method under SLA and margin guardrails.
Pluggable seams for rate shopping and address validation.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RoutingDecision:
    supplier_id: Optional[int]
    ship_carrier: Optional[str]
    ship_service: Optional[str]
    explanation: str
    simulated: bool = True


class RoutingEngine:
    def __init__(self, guardrails: Optional[Dict[str, Any]] = None):
        self.guardrails = guardrails or {}

    def validate_address(self, region: Dict[str, Any]) -> bool:
        # TODO: plug USPS/Shippo/Google validation
        if not region:
            return False
        country = (region.get("country") or "").strip()
        state = (region.get("state") or "").strip()
        postal = (region.get("postal_code") or "").strip()
        if not country:
            return False
        # Minimal validation heuristics
        if country.upper() == "US":
            if not state or len(state) not in (2, 3):
                return False
            if not postal or len(postal) < 5:
                return False
        return True

    def rate_shop(self, region: Dict[str, Any], weight_oz: float) -> Dict[str, Any]:
        # TODO: integrate EasyPost/Shippo; return best rate
        # Simulate a few options
        options = [
            {"carrier": "UPS", "service": "Ground", "cost_cents": 999},
            {"carrier": "USPS", "service": "Priority", "cost_cents": 1299},
            {"carrier": "FedEx", "service": "HomeDelivery", "cost_cents": 1399},
        ]
        max_cost = self.guardrails.get("max_cost_cents")
        if isinstance(max_cost, int):
            options = [o for o in options if o["cost_cents"] <= max_cost] or options
        # Pick lowest cost among candidates
        best = sorted(options, key=lambda o: o["cost_cents"])[0]
        return best

    def select_supplier(self, items: List[Dict[str, Any]]) -> Optional[int]:
        # TODO: integrate suppliers/offers inventory + cost tables
        if not items:
            return None
        return 1  # stub supplier id

    def route(self, order: Dict[str, Any]) -> RoutingDecision:
        region = order.get("buyer_region", {})
        if not self.validate_address(region):
            return RoutingDecision(
                supplier_id=None,
                ship_carrier=None,
                ship_service=None,
                explanation="ADDRESS_FAIL: invalid region",
                simulated=True,
            )
        supplier_id = self.select_supplier(order.get("items", []))
        rate = self.rate_shop(region, weight_oz=order.get("weight_oz", 16))
        return RoutingDecision(
            supplier_id=supplier_id,
            ship_carrier=rate["carrier"],
            ship_service=rate["service"],
            explanation="Simulated routing decision",
            simulated=True,
        )
